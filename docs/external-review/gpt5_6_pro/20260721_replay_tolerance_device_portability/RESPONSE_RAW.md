# GPT-5.6 Pro Response — Replay Tolerance Device Portability

Received 2026-07-21. Archived verbatim as delivered. LaTeX markup was mangled in
transport; formulas are reconstructable from context. No content is edited,
reordered or summarized here.

---

1. Is `1e-6` a defensible device- and width-portable bound?
No. It is defensible only as a narrow same-device, same-shape replay gate for the currently registered CUDA/width-16 execution path. It is not a general float32 portability bound.
The code confirms the numerical structure described in the question:

* `REPLAY_TOLERANCE` is one scalar `1e-6`.
* Each transformed-normal mark component is compared separately.
* `event_joint` is then formed as one categorical log-probability plus the sum of eight mark-component log-probabilities.
* `validate_replay` applies the same scalar tolerance to every continuous quantity, including both the individual components and that nine-factor joint.

That is mathematically inconsistent as a portability contract: a derived sum is given no more error allowance than any one summand. The same issue also exists for `primitive_joint`, which sums up to six primitive component errors but is checked against the same scalar.
I could verify the definitions and accumulation relationship from committed code. The exact reported CPU and width-one measurements are not committed as a reproducible artifact in the reviewed paths, so I cannot independently certify the numerical values `1.91e-6` and `1.19e-6`; they are nevertheless entirely consistent with what the code measures.
There is another correction to the premise: the current CPU path is not blocked solely by the tolerance. The formal runner explicitly rejects every device except CUDA and forbids CPU fallback. Enabling CPU formal execution would therefore be a separate frozen execution-contract change.
Principled replacement
Keep the existing `1e-6` bound for each individual replayed factor and ordinary continuous state unless separate evidence requires changing it. Replace the joint scalar check with a compositional bound.
For an event row, let
[
J=c+\sum_{j=1}^{8}m_j
]
and let (\delta_c) and (\delta_{m_j}) be the replay-minus-collection component differences. Require:
[
|\delta_c|\le 10^{-6},
\qquad
|\delta_{m_j}|\le10^{-6}\quad\forall j,
]
and:
[
|J_{\mathrm{replay}}-J_{\mathrm{stored}}|
\le
|\delta_c|
+\sum_{j=1}^{8}|\delta_{m_j}|
+\gamma_9
\left(
\sum |f_{\mathrm{stored}}|
+
\sum |f_{\mathrm{replay}}|
\right),
]
where (u=2^{-24}) is float32 unit roundoff and
[
\gamma_9=\frac{9u}{1-9u}\approx5.37\times10^{-7}.
]
This is not fitted to the observed `1.91e-6`; it follows from the registered per-factor tolerance plus a conservative float32 summation allowance. Apply the analogous rule to `primitive_joint` using the actual number of active primitive factors.
An even clearer implementation is to validate both stored and replayed joints against a float64 recomputation from their recorded factors, while retaining the componentwise replay checks. The joint then tests correct factor assembly, rather than demanding that nine accumulated float32 terms remain within a one-component tolerance.
If implementation simplicity requires a fixed event-joint absolute ceiling, `1e-5` is the smallest clean conservative value derived from nine factors each bounded by `1e-6`, with a small reduction allowance. The compositional row-wise bound is preferable because it scales with the actual factors and preserves more diagnostic precision.
2. One scalar or per-factor?
Use per-factor tolerances and derived joint rules. Do not globally relax the current scalar.
The frozen replay contract should distinguish four classes:

1. Exact semantic invariants
These remain exact zero-error checks:
   * event support and factor masks;
   * categorical event action;
   * action and lifecycle masks;
   * kind support;
   * detach status;
   * discrete actions, order and membership ownership where applicable.
The current code already separates several of these as exact mismatches before applying the numerical tolerance.
2. Ordinary continuous replay state
Retain `1e-6` for:
   * hidden states;
   * values;
   * event inputs;
   * reconstructed marks;
   * primitive component log-probabilities;
   * categorical component log-probabilities;
   * each individual transformed-mark component.
3. Derived primitive joint
Bound it by the sum of the eligible primitive-component differences plus its reduction-rounding allowance.
4. Derived event joint
Bound it by the categorical difference plus all eight mark-component differences plus its reduction-rounding allowance.

This preserves the strongest useful guarantee: every likelihood factor is reconstructed closely and the joint contains exactly the registered factors. It avoids allowing a large joint tolerance to conceal a defective component.
The evaluation artifact must also stop collapsing all replay errors into one `maximum_error`. The current runner takes `max(errors.values())` and hardcodes `<=1e-6` in both evaluation generation and artifact validation. A per-factor contract requires serializing the named error dictionary, the derived joint bound, and a normalized pass result.
3. Does relaxing the joint tolerance weaken a scientific guarantee?
Changing only the derived-joint rule as above does not materially weaken the scientific guarantee. It corrects a misspecified numerical guarantee.
The scientific purpose of replay validation is to ensure that:

* the stored behavior likelihood has the registered factorization;
* masks and actions select the same factors;
* PPO begins from a ratio indistinguishable from one up to float32 reconstruction noise.

The event PPO ratio is:
[
\exp\left(
\log\pi_{\mathrm{replay}}
\log\pi_{\mathrm{old}}
\right).
]
Even a conservative joint discrepancy of (10^{-5}) induces at most:
[
e^{10^{-5}}-1\approx1.0\times10^{-5}
]
of spurious importance-ratio displacement. That is about (0.005%) of the PPO clipping distance `0.20`; it cannot plausibly manufacture the registered arm effect. The individual factor checks remain at `1e-6`, so an omitted mark component, wrong mask, incorrect Jacobian, stale action, or wrong factor support would still fail decisively.
There are, however, three guarantees that would be weakened by an indiscriminate global relaxation:

1. Wrong recurrent reconstruction could be masked.
Do not raise the tolerance for hidden state, event input, value and component likelihoods merely because the joint is a sum.
2. Width-one fork reconstruction could be improperly admitted.
The fork engine's natural-action branch has a stronger requirement: it must reproduce the factual continuation exactly, and the clean implementation can reconstruct at the registered factual width 16. A relaxed replay tolerance must not be used to bless a width-one reconstruction when width-16 reconstruction is bitwise exact.
3. Resume equality could be weakened accidentally.
`RESUME_TOLERANCE=1e-7` is a separate same-checkpoint continuation invariant. It should remain unchanged. Replay portability and interrupted-run reproducibility are different guarantees.

Also, allowing CPU formal execution is not implied by changing this constant. Current code hard-requires CUDA; a CPU formal run would need a separately frozen backend contract. All arms and paired replicates should use the same backend and thread configuration—never a mixture of CPU and CUDA—so device-dependent optimization trajectories cannot become an arm or replicate confound.
So the plain answer is:
A per-factor plus compositional-joint rule does not weaken an important scientific guarantee. A broad global tolerance increase, or using it to relax fork/resume equivalence, would.
4. Does the checkpoint contract need to change?
Yes. The registered scientific contract and all artifacts that embed it must change before any formal checkpoint is written.
`registered_contract()` currently serializes the scalar replay tolerance under its optimization fields. Checkpoints store the complete registered contract, and `load_checkpoint` rejects any inequality.
Replace the scalar with an explicit structure such as:

```text
replay_tolerances:
  exact_fields: [...]
  continuous_component_atol: 1e-6
  categorical_component_atol: 1e-6
  mark_component_atol: 1e-6
  primitive_joint_rule: component_sum_plus_float32_reduction
  event_joint_rule: categorical_plus_8_marks_plus_float32_reduction
  float32_unit_roundoff: 5.960464477539063e-8

```

Old smoke or development checkpoints should then fail strict contract loading. No compatibility shim should be added.
A checkpoint serialization schema-version increment is not mathematically required if the payload layout itself is unchanged; strict registered-contract inequality already establishes the boundary. A scientific contract revision should nevertheless be explicit. If the evaluation artifact changes from one `maximum_error` to named per-factor errors—as it should—the evaluation artifact schema must also be incremented.
Changing the Python constant alone is insufficient. The following hardcoded paths must be updated consistently:

* `validate_replay`;
* formal evaluation's `replay_maximum <= 1e-6`;
* `validate_operational_records`' corresponding hardcoded comparison;
* `IMPLEMENTATION_PLAN.md`;
* the registered-contract dictionary and focused tests.

Because no formal training has begun, this is the correct preregistration boundary at which to make the correction.

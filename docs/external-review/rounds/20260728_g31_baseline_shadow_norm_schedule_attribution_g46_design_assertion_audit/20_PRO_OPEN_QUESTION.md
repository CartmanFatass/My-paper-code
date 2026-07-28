# External Pro: G46 baseline-shadow norm schedule attribution design assertion audit

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_AUDIT
round=20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
```

You are External GPT-5.6 Pro, the exclusive scientific decision authority for
this bounded design audit. Read exactly the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the pushed stage commit. Do not reactivate
G33, reinterpret earlier accepted units, implement code, run proof/nonformal/
formal compute, edit CDC, or select a different successor.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_formal_result_review/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_formal_result_review/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md`

## Exact design question

Can a conclusion-bearing matched post-anchor comparison be frozen between:

- `NATIVE6_G31_NO_READ_BASELINE_SHADOW_NORM`, the accepted G45 route whose
  immediate and successor residuals are target-only but whose raw equal-mean
  credit direction is rescaled to the norm of a local baseline-conditioned
  counterfactual; and
- `NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM`, the identical target-only route
  using the literal unrescaled equal-mean credit gradient, with no
  baseline-output read into residual, direction, or scalar norm?

Both arms retain identical accepted G40 common fast anchors, G41 no-slow
projection, native-six actor and log_std, immediate and realized-successor
targets, separate channel centering, independent per-channel RMS scaling,
literal `0.5*(g_I+g_S)`, common entropy, baseline module and target-fitting
losses, baseline parameter/Adam exposure, source ledgers and action streams,
PPO passes and optimizer-step exposure, evaluation/confidence plan, and
final-only checkpoints.

The only treatment is the baseline-derived dynamic scalar credit-norm schedule
versus the literal raw equal-mean credit-gradient norm.

## Frozen actor-credit laws

For both arms, construct target-only residuals:

```text
x_I = r_t
x_S = G_(t+1)
v_raw = 0.5 * (g_I + g_S)
```

Reference arm, using only its own current pre-update state and trajectory:

```text
m_B = ||v_READ,cf||_2
v_REF = 0                         if m_B = 0
        (m_B / ||v_raw||_2)v_raw  if m_B > 0 and ||v_raw||_2 > 0
```

Raw-norm null:

```text
v_RAW = v_raw
baseline_read_into_actual_residual=0
baseline_read_into_actual_direction=0
baseline_read_into_actual_scalar_norm=0
baseline_counterfactual_calls=0
learned_or_tunable_scale=0
```

Common entropy is added once after these credit-gradient rules and is never
rescaled.

## Zero, cancellation, activation and estimand rules

- If `m_B=0` and `||v_raw||_2>0`, the reference credit gradient is exact zero
  and the raw arm keeps its raw gradient; this is valid scalar treatment.
- If both norms are zero, both assigned credit gradients are exact zero and the
  pass is valid but inactive.
- If `m_B>0` and `||v_raw||_2=0`, the norm-matched direction is undefined and
  the pass is invalid before either optimizer.
- Any nonfinite residual, gradient, norm, or assigned row is invalid.
- Zero credit gradients do not skip baseline updates, entropy, or actor/head
  Adam exposure.
- Define `m_raw=||v_raw||_2` and
  `q_norm=0` when `m_B=m_raw=0`, otherwise
  `q_norm=max(m_B,m_raw)/abs(m_B-m_raw)`.
- Require at least one valid `q_norm > 1e-6` treatment-active pass in the
  nonformal exercise and at least one such pass in each accepted-anchor formal
  replicate `0|1|2`.
- When both assigned credit gradients are nonzero, their unit directions must
  agree under one frozen proof tolerance; any directional discrepancy is
  invalid because G46 is a scalar-schedule attribution.

The primary estimand is:

```text
Delta_shadow_norm = U_SHADOW_NORM - U_RAW_NORM
materiality_and_noninferiority_margin=0.05
```

Positive values favor the baseline-derived scalar schedule.

## Claim ceilings and first-match branches

A raw-norm sufficiency result may support only that the baseline-derived scalar
credit-norm schedule is removable from the actor-credit path under G46-P0 while
the baseline module, target fitting, parameters and optimizer exposure remain
matched shadow controls. It may not yet claim structural baseline-module
deletion. A positive result may support only a source-local finite-budget access
or material-utility advantage for the local scalar schedule over the literal
raw-norm null. Neither outcome adjudicates realized-tail targeting,
decomposition, separate centering, independent scaling, the common anchor,
recurrence, UAV mechanisms, or G33.

Return exactly one first-match branch:

```text
INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_ATTRIBUTION_G46
SOURCE_OR_REFERENCE_ACCESS_FAILURE_G46
RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46
BASELINE_SHADOW_NORM_SCHEDULE_ADVANTAGE_G46
MIXED_UNDERPOWERED_BASELINE_SHADOW_NORM_ATTRIBUTION_G46
```

The sufficiency branch requires both arms to pass the inherited access contract
and every reference-minus-raw primary/component UCB to be `<=0.05`. The
advantage branch requires reference access and either confident raw-arm failure
or `LCB95(Delta_shadow_norm)>0.05` with every capacity-specific primary LCB
strictly positive.

## Evidence and complexity ceilings

```text
nonformal_real_transitions<=14592
nonformal_optimizer_steps<=40
nonformal_wall_clock<=1200_seconds
formal_real_transitions<=396288
formal_optimizer_steps<=1200
formal_wall_clock<=28800_seconds
formal_replicates=0|1|2
process_profile_balance=16/16/16
episodes_per_cell=48
formal_bootstrap_draws=10000
```

Use the inherited three accepted-anchor replicates, exact process/profile
balance, whole-episode paired confidence, equal capacity weighting, no
exclusions, and the smallest conclusion-bearing inventory consistent with the
inherited absolute-access gates. These are ceilings and do not authorize any
implementation or compute.

## Required response

Return one first-match branch exactly, state whether the design is frozen,
identify any missing or contradictory contract field without inventing values,
and if frozen state the smallest next boundary. Do not run compute, implement,
edit CDC, or select a different successor.

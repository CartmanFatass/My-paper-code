# External Pro: G46 code-science alignment audit

review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
compute_budget=zero
audit_target_commit=ef3a2fa273d1506c2bc88f50db8e06810e946809
implementation_code_commit=ef3a2fa273d1506c2bc88f50db8e06810e946809
accepted_design_source_commit=8cb6fb8872e64c93f6d699ad24dd549704462aaa
correction_stage_commit=dd762c236066f2673981f20bc1d2f6664961dea7
formal_compute_started=false
nonformal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY

You are External GPT-5.6 Pro, the exclusive scientific authority for this bounded
contract diff. Read exactly the paths in 01_SHARED_SOURCE_MANIFEST.md from the
exact audit target commit. Do not implement, compute, redesign, edit CDC,
authorize a run, select a successor, reopen earlier retired directions, or
reactivate G33. Stop after one scoped disposition.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_contract_correction_clarification/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_contract_correction_clarification/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_contract_correction_clarification/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46.py`
- `scripts/run_continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46_test.py`
- `tests/run_continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_CODE_SCIENCE_INDEX.md`

## Exact question

Does the accepted implementation at
ef3a2fa273d1506c2bc88f50db8e06810e946809 instantiate the frozen G46
post-anchor comparison between:

- NATIVE6_G31_NO_READ_BASELINE_SHADOW_NORM: target-only immediate and
  realized-successor credit, with the reference arm's raw equal-mean credit
  direction rescaled only to its own detached local baseline-counterfactual
  scalar norm; and
- NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM: the identical target-only route
  using the literal raw equal-mean credit norm, with zero baseline-output reads
  into actual residual, direction, scalar, action/logprob, checkpoint selection,
  and evaluation metric?

The only intended treatment is the corrected baseline-derived dynamic scalar
credit-norm schedule versus the literal raw equal-mean norm.

## Frozen conformance points

1. Both arms must retain identical accepted G40 common fast anchors, G41
no-slow projection, native-six actor/log_std, immediate and realized-successor
targets, separate channel centering, independent per-channel RMS scaling, literal
0.5*(g_I+g_S), common entropy added once after credit rules, baseline module and
target-fitting losses, baseline parameter/Adam exposure, source/RNG/action
streams, PPO passes/optimizer exposure, evaluation/confidence plan, and
final-only checkpoints.

2. Target-only credit laws are x_I=r_t, x_S=G_(t+1), v_raw=0.5*(g_I+g_S).
The reference arm uses m_B=||v_READ,cf||_2 from its own current pre-update
trajectory and assigns v_REF=0 when m_B=0, otherwise
v_REF=(m_B/||v_raw||_2)*v_raw when m_B>0 and ||v_raw||_2>0.
The raw arm assigns v_RAW=v_raw. Any nonfinite residual/gradient/norm/row is
invalid. m_B>0 with m_raw=0 is invalid before either optimizer; zero credit
does not skip baseline, entropy, or Adam exposure.

3. Corrected q_norm is exact and piecewise:
finite nonnegative norms are required; m_B=m_raw=0 gives q_norm=0 valid
inactive; m_B=m_raw>0 gives q_norm=0 valid inactive; m_B=0,m_raw>0 gives
q_norm=1 valid active; m_B>0,m_raw=0 is undefined and invalid; positive
unequal norms give abs(m_B-m_raw)/max(m_B,m_raw). Treatment is active only
under strict q_norm>1e-6; equality at 1e-6 is inactive.

4. When both assigned credit gradients are nonzero, flatten in the frozen
actor-plus-log_std order, cast to float64, normalize without epsilon, and
require inclusive ||u_REF-u_RAW||_2<=1e-6. Any greater distance or nonfinite
norm/coordinate is invalid. If either assigned gradient is zero, do not
evaluate the direction rule; use the zero/cancellation table.

5. The implementation must enforce actual callable-path and serialized
evidence gates: finite live immediate/successor channels, exact actor-group
inventory with each group live in at least one channel, both baseline-output
rows and shared-trunk liveness, zero raw-arm baseline reads, independent
activation evidence from pre-update state, strict active-pass evidence in
nonformal and formal replicates 0|1|2, and rejection of stored flags, collinear
or vacuous treatment, missing replicas, tampered payloads, wrong branch,
wrong source, wrong checkpoint inventory, and nonfinite values.

6. Both complete trajectories and update plans must be materialized before fixed
reference-then-raw updates. Initial tensors, targets, baseline losses,
gradients and entropy must match bitwise; only residual law may differ.
Actor/head Adam is persistent with lr=1e-3, betas=.9/.999, eps=1e-8,
weight_decay=0, no clipping/minibatches/reset, one step per pass and final-only
checkpoints. The raw arm remains baseline-fitted for exposure.

7. Frozen resource and confidence contract: H=48, K_search=0,
hypothetical_transitions=0, C++ toy backend with no Python fallback,
fixed process/worker controls and deterministic preassigned-index merge;
nonformal ceilings <=14592 transitions, <=40 optimizer steps, <=1200 seconds;
formal <=396288 transitions, <=1200 optimizer steps, <=28800 seconds;
formal replicates 0|1|2, process/profile balance 16/16/16, 48 episodes/cell,
10000 paired hierarchical bootstrap, inherited access floors, estimand
Delta_shadow_norm=U_SHADOW_NORM-U_RAW_NORM, margin 0.05, 95-percentile paired
confidence and exact first-match branches.

8. Reload must revalidate the frozen contract, source/provenance identity,
both-arm evidence, activation, and final-only artifact inventory. Formal
admission remains closed until a fresh exact ALIGNED target/stage, same-source
nonformal preflight and exact authorization token. Readiness is proof-only and
scientific iteration cost is zero.

Determine whether malformed parameters, gradients, storage, RNG, checkpoints,
diagnostics, baseline reads, or hidden value proxies can bypass these gates.
Do not assess style, performance, workflow design, or unregistered scope.

Return exactly one disposition:

AUDIT_DISPOSITION=ALIGNED
AUDIT_DISPOSITION=MISMATCH
AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY

Return MISMATCH only with the exact frozen assertion, conflicting code path or
behavior, and smallest in-contract correction. Return SCIENTIFIC_AMBIGUITY only
for a previously unstated result-changing scientific choice that prevents
judgment.

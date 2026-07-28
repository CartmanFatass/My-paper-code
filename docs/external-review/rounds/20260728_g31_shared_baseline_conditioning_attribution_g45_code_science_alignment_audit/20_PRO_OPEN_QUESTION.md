# External Pro: G45 code-science alignment audit

review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
compute_budget=zero
audit_target_commit=1c38e387fa7fe90dc6446177eb69146a12a29a20
implementation_code_commit=1c38e387fa7fe90dc6446177eb69146a12a29a20
accepted_design_source_commit=5f99e484f172a53e98307e20ed5ac0b6af40638d
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_INDEX.md
formal_compute_started=false
nonformal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY

You are External GPT-5.6 Pro, the exclusive scientific authority for this
bounded contract diff. Read exactly the paths in
01_SHARED_SOURCE_MANIFEST.md from the exact pushed audit target commit. Do not
implement, compute, redesign, edit CDC, authorize a run, reopen G44, select a
successor, or reactivate G33. Stop after one scoped disposition.

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
- `docs/report/ITERATION_34.md`
- `docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/20_PRO_OPEN_QUESTION.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45.py`
- `scripts/run_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45_test.py`
- `tests/run_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py`
- `scripts/run_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py`
- `ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`
- `ha_ctse_process/continuous_roster_native_six_g31_db_norm_schedule_attribution_g43.py`

## Exact question

Does the accepted implementation at
1c38e387fa7fe90dc6446177eb69146a12a29a20 instantiate the frozen G45
post-anchor comparison between:

- NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_READ, which subtracts the shared
  true-current-state baseline outputs from the immediate and realized-successor
  actor-credit residuals; and
- NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ, which retains the
  identical baseline module, true-current-state inputs, target fitting, loss,
  parameters, optimizer exposure and checkpoint inventory but reads neither
  baseline output into actor credit?

The only intended treatment is baseline-output subtraction into actor credit
versus zero actor read of those outputs. The implementation must retain the
accepted G44 independent channel centering/RMS normalization and literal
0.5*(g_I+g_S), and must use only a detached local READ counterfactual scalar
credit norm to match the NO_READ actor-step scale. This round is a contract
diff, not a quality review.

## Frozen conformance points

1. Projection must clone one accepted G40 common anchor through the accepted
   G44/G41 route bitwise into storage-disjoint READ and NO_READ arms, preserve
   actor/log-std/shared-baseline bytes and optimizer order, consume no model
   RNG, and add no learned scale, slow critic, DB state or arm-specific
   parameter/statistic.
2. READ credit must be exactly
   r_t-stopgrad(b_I(xi_t)) and
   G_(t+1)-stopgrad(b_S(xi_t)); NO_READ credit must be exactly r_t and
   G_(t+1) from rewards/terminals only. Baseline targets, target fitting,
   baseline losses, shared parameters and baseline Adam exposure remain
   identical. Every arm/pass must bind both residual laws, means, sums of
   squares, RMS scales, normalized-row digest, 384-row count, mask, episode,
   true-current-state, target and baseline-output digests.
3. Both arms must retain accepted G44 separate centering, independent RMS
   scaling, literal 0.5*(g_I+g_S), common entropy once after the gate, two
   persistent PPO passes, realized-successor G31 credit and no slow critic.
   Normalization is computed once before both passes with no active-count
   weighting, epsilon, row exclusion or between-pass recomputation.
4. NO_READ may compute only its own local detached READ counterfactual scalar
   credit norm. No counterfactual vector or coordinate may be serialized,
   assigned, or used outside that norm. Positive counterfactual norm with zero
   NO_READ raw direction fails before either optimizer; zero counterfactual
   norm assigns exact-zero credit without skipping common entropy, baseline or
   Adam exposure. The gate must match the frozen norm tolerance exactly.
5. Every pass must prove finite globally live immediate/successor channels,
   exact registered actor-group inventory with each group live in at least one
   channel, immediate/successor baseline-output and shared-trunk liveness, and
   zero NO_READ reads into residual, gradient direction, action/logprob,
   checkpoint selection and evaluation metric. The callable boundary must
   enforce this from actual code paths, not only a declarative certificate.
6. Activation evidence must come only from READ pre-update state and
   reconstruct both baseline RMS values, q_baseline, READ and local NO_READ
   counterfactual norms, dot product and unit-direction distance. NO_READ
   evidence-read count is zero. Require one active pass in nonformal and one
   active pass in each formal replicate 0,1,2; reject stored flags, collinear
   or vacuous treatment and missing replicate evidence.
7. Both complete trajectories and update plans must be materialized before
   fixed READ then NO_READ updates. Initial tensors, targets, baseline losses,
   gradients and entropy must match bitwise; only residual law may differ.
   Actor/head Adam is persistent with lr=1e-3, betas=.9/.999, eps=1e-8,
   weight_decay=0, no clipping/minibatches/reset, one step per pass and
   final-only checkpoints. The no-read baseline remains fitted for exposure.
8. Frozen seeds, budgets, backend, process and confidence contracts must be
   bound: H=48, K_search=0, no hypothetical transitions, C++ toy backend with
   no Python fallback, fixed 1..6 workers and one native/PyTorch thread per
   worker, deterministic preassigned-index merge; nonformal <=14592 real
   transitions/40 optimizer steps/1200 seconds and formal <=396288/1200/
   28800 seconds; formal 3 replicates, 100 updates per arm, 48 episodes/cell,
   10000 paired hierarchical bootstrap. Access floors, READ-minus-NO_READ
   estimand, 0.05 margin, 95-percentile paired confidence and exact
   first-match branch labels must remain frozen.
9. Checkpoint/artifact reload must revalidate residual routes, both-arm
   evidence, shadow certificate, activation, exact source/provenance and
   final-only inventory. Formal admission must remain closed until a fresh
   exact ALIGNED target/stage, same-source nonformal preflight and the exact
   authorization token. Readiness is proof-only and has zero scientific cost.

Determine whether malformed parameters, gradients, storage, RNG, checkpoints,
diagnostics, baseline reads, or a hidden value proxy can bypass these gates.
Do not assess style, performance, workflow design, or unregistered scope.

Return exactly one disposition:

AUDIT_DISPOSITION=ALIGNED
AUDIT_DISPOSITION=MISMATCH
AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY

Return MISMATCH only with the exact frozen assertion, conflicting code path or
behavior, and smallest in-contract correction. Return SCIENTIFIC_AMBIGUITY
only for a previously unstated result-changing scientific choice that prevents
judgment.

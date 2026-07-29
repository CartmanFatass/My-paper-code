# External Pro: G51 phase-A shadow-baseline module reduction design assertion audit

```text
semantic_author=research_operations_manager
artifact_scope=reviewer_visible_design_boundary
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_AUDIT
round=20260729_g31_phase_a_shadow_baseline_module_reduction_g51_design_assertion_audit
source_commit=044d9690fa19aa07b8e68bf5cbb2a159c19be8c1
design_audit_compute=0
valid_iteration_cost=zero
```

You are External GPT-5.6 Pro, the exclusive scientific decision authority
inside this bounded design question. Read exactly the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the pushed `source_commit`. Do not
implement code, run proof execution or formal compute, edit CDC, reactivate
G33, or select a different successor. Do not infer beyond the exact G50
predecessor and the G51 boundary below.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_INDEX.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260729_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_FORMAL_RESULT.md`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_formal_result_review/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md`

## Exact design assertion

Assess only whether an exact structural comparison can be frozen between these
two arms after the accepted G50 route:

`G50_FRESH_SINGLE_IMMEDIATE_WITH_PHASE_A_SHADOW_BASELINE` retains the shared
two-output baseline module, its true-state input consumer, immediate-baseline
target-fitting loss, baseline parameters and Adam state, optimizer membership,
liveness/diagnostic records and baseline checkpoint fields, although no
baseline output enters actor credit; and
`G50_FRESH_SINGLE_IMMEDIATE_WITHOUT_PHASE_A_BASELINE_MODULE` uses the identical
actor-credit route with the entire phase-A baseline module and all
baseline-only training/checkpoint state removed.

The intended treatment deletes exactly:

- the `credit_baselines` module and its true-state input consumer;
- immediate-baseline target and MSE loss;
- baseline parameters, gradients, Adam slots and optimizer membership;
- baseline liveness/diagnostic records;
- baseline checkpoint keys and artifact schema fields.

Both arms retain exactly the same fresh native-six actor/log_std
initialization, G49 single-immediate actor credit in phase A, immediate-target
centering and population-RMS normalization, common entropy, source ledgers,
action noise and environment trajectories, PPO passes and actor optimizer
exposure, the 100-update phase boundary and fresh phase-B Adam, the G49
single-immediate phase B, and the final-only actor checkpoint contract.
No replacement baseline, critic, learned scale, constant filler, optimizer
compensation or utility threshold is permitted.

## Required identification test

Define `D_G51` as the maximum exact difference across:

- actor/log_std assigned gradients;
- actor parameter bytes;
- actor Adam step, exp_avg and exp_avg_sq bytes;
- pre-tanh means, actions and token/joint log-probabilities;
- reward, roster and lifecycle traces;
- phase-boundary projected actor bytes;
- phase-B actor/Adam trajectories;
- canonical final actor-checkpoint projection.

The exact-removability branch requires `D_G51=0`. Require zero baseline reads
into actor gradient, entropy, action/log-probability, checkpoint selection,
evaluation and result selection; bitwise-equal actor updates and Adam states;
and equal actions and registered traces under frozen existing tolerances.
Reject parameter ordering, shared storage, global clipping, joint
normalization, optimizer-wide scheduling and checkpoint-selection coupling.

## Complexity ceiling and claim ceiling

Seek a zero-trajectory static dependency and per-parameter Adam-factorization
proof first. If a dynamic witness is indispensable, use at most one accepted
G50 fresh initialization and one shared 8-episode × 48-step stored phase-A
batch, with:

```text
real_transitions<=384
PPO_passes_per_arm=2
actor_optimizer_steps_per_arm=2
total_optimizer_steps<=4
bootstrap_resamples=0
formal_statistical_run=false
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
wall_clock<=1200_seconds
```

The same stored trajectory must feed both paths; duplicated environment
interaction is unnecessary. A positive result may support only exact removal of
the registered G50 phase-A shadow-baseline apparatus. It may not establish
arbitrary baseline redundancy, removal of immediate normalization or entropy,
uninterrupted-training sufficiency, UAV transport or universal memorylessness.

## Required response

Return these sections in order:

1. `DESIGN_ASSERTION_CONFORMANCE`
2. `IDENTIFICATION_AND_DEPENDENCY_RESULT`
3. `COUNTEREXAMPLES_AND_CLAIM_CEILING`
4. `EVIDENCE_AND_COMPLEXITY_DISPOSITION`
5. `PORTFOLIO_AND_NEXT_ACTION`
6. `EXECUTABLE_BOUNDARY`
7. `中文简报`

Then return exactly one separate line:

`DESIGN_DISPOSITION=PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51`

or

`DESIGN_DISPOSITION=UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51`

or

`DESIGN_DISPOSITION=NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51`

or

`DESIGN_DISPOSITION=INVALID_G50_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51`

or

`DESIGN_DISPOSITION=SCIENTIFIC_AMBIGUITY`.

The response must contain all seven sections and exactly one disposition line.
Do not return only a generic audit token. The operator owns no scientific
interpretation, implementation, Git, browser transport or compute.

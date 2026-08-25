# External Pro: G45 shared-baseline conditioning attribution design assertion audit

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_AUDIT
round=20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit
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
- `docs/report/ITERATION_34.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_FORMAL_RESULT_96E35DD.md`
- `docs/external-review/rounds/20260727_g44_channel_norm_formal_result_review_v1/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_g44_channel_norm_formal_result_review_v1/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260727_g44_channel_norm_formal_result_review_v1/20_PRO_OPEN_QUESTION.md`

## Exact design question

Can a conclusion-bearing matched post-anchor comparison be frozen between:

- `NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_READ`, the accepted G44 route whose
  immediate and successor actor-credit residuals subtract their shared
  true-current-state baseline outputs; and
- `NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ`, the identical route
  with the same baseline module, inputs, target-fitting losses, parameters,
  optimizer group, Adam exposure and checkpoint inventory, but with zero
  baseline-output reads into the actor-credit residuals?

The only intended treatment is state-conditioned baseline subtraction into
actor credit versus no actor read of those baseline outputs.

## Frozen residual laws

Reference arm:

```text
x_I,READ  = r_t - stopgrad(b_I(xi_t))
x_S,READ  = G_(t+1) - stopgrad(b_S(xi_t))
```

No-read null:

```text
x_I,NO_READ = r_t
x_S,NO_READ = G_(t+1)
```

Both arms then use the same frozen pipeline: separate channel centering,
independent per-channel RMS scaling, literal `0.5*(g_I+g_S)`, common entropy
added once and two persistent PPO passes.

## Baseline inventory and shadow isolation

Both arms retain byte-identical shared two-output baseline graph, true-current-
state inputs, baseline targets, baseline losses, parameter order and baseline
Adam state/exposure. In the no-read arm all of the following are zero:

```text
baseline_read_into_actor_residual=0
baseline_read_into_actor_gradient_direction=0
baseline_read_into_action_or_logprob=0
baseline_read_into_checkpoint_selection=0
baseline_read_into_evaluation_metric=0
```

The baseline remains shadow-trained only to match capacity and optimizer
exposure.

## Credit-step scale control and activation

Because baseline subtraction can change direction and global actor-credit norm,
the no-read arm must match its credit-gradient norm to a local baseline-read
counterfactual computed on its own pre-update model and trajectory. Only the
detached scalar norm may be used. The counterfactual vector cannot be assigned,
serialized as an actor interface, or affect the no-read direction. Common
entropy and baseline gradients are added or applied unchanged after the gate.

Using only the reference arm's pre-update state, construct the reference
baseline-conditioned credit direction and no-baseline-read counterfactual
credit direction. Require both at least one baseline output with centered RMS
greater than `1e-6`, unit-direction distance greater than `1e-6`, and positive
finite credit norms. The actual no-read arm supplies no activation evidence.

Required scope:

```text
nonformal: at least one treatment-active pass
formal: at least one treatment-active pass in each accepted-anchor replicate 0|1|2
```

## Primary estimand and claim ceilings

```text
Delta_baseline = U_READ - U_NO_READ
materiality_and_noninferiority_margin=0.05
```

Positive values favor actor use of the shared true-state baseline. A no-read
sufficiency result may support only that state-conditioned baseline subtraction
is removable from the actor-credit direction under G45-P0 while the baseline
module, its target fitting, optimizer exposure and local counterfactual scalar
norm remain retained as matched controls. It may not establish that the
baseline module or centralized true-state information can already be deleted.

A positive reference result may support only that shared true-current-state
baseline conditioning supplies a source-local finite-budget access or
material-utility advantage over the exact shadow-trained no-actor-read null.
Neither result may establish necessity or redundancy of realized-tail targets,
decomposition, separate centering, independent scaling, equal-mean composition,
the common anchor, recurrence, UAV mechanisms or G33.

## Frozen first-match branches

Return exactly one of these bounded branches:

```text
INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45
SOURCE_OR_REFERENCE_ACCESS_FAILURE_G45
SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45
SHARED_TRUE_STATE_BASELINE_CONDITIONING_ADVANTAGE_G45
MIXED_UNDERPOWERED_SHARED_BASELINE_CONDITIONING_G45
```

The sufficiency branch requires both arms to pass the complete inherited access
contract and every READ-minus-NO_READ primary/component UCB to be `<=0.05`.
The advantage branch requires reference access and either confident no-read
failure or `LCB95(Delta_baseline)>0.05` with every capacity-specific primary
LCB strictly positive.

## Evidence-complexity ceiling

These are ceilings, not defaults or compute authorization. Choose the smallest
conclusion-bearing inventory consistent with three accepted-anchor replicates,
exact process/profile balance, whole-episode paired confidence and inherited
absolute-access gates:

```text
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
nonformal_real_transitions<=14592
nonformal_optimizer_steps<=40
nonformal_wall_clock<=1200_seconds
formal_real_transitions<=396288
formal_optimizer_steps<=1200
formal_wall_clock<=28800_seconds
```

These ceilings authorize no implementation, Git operation, nonformal run or
formal run.

## Required response sections

Return exactly these sections and one bounded design disposition:

1. `REGISTERED_DESIGN_CONFORMANCE`
2. `DESIGN_SCIENTIFIC_DISPOSITION`
3. `IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES`
4. `CDC_PORTFOLIO_LEDGER_EDITS`
5. `DESIGN_VALID_DISPOSITION`
6. `CURRENT_SCHEDULED_ACTION_IF_CONTINUE`
7. `EXECUTABLE_DESIGN_BOUNDARY`
8. `CHINESE_SUMMARY`

The terminal design disposition must be one of:

```text
DESIGN_VALID_DISPOSITION=CONTINUE
DESIGN_VALID_DISPOSITION=CLOSE_NO_EXECUTABLE_CANDIDATE
DESIGN_VALID_DISPOSITION=COMPLETE_BALANCE_EXHAUSTED
```

If `CONTINUE`, name only this exact G45 action. Do not authorize code or
compute, and do not reorder, compress or retire the preserved portfolio.

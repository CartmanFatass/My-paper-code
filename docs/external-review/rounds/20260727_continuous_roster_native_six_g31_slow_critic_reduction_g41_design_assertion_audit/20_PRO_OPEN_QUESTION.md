# External Pro: G41 standalone slow-critic design assertion audit

```text
semantic_author=research_operations_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_AUDIT
round=20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_design_assertion_audit
reference_formal_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
```

## Authority and exact task

You are External GPT-5.6 Pro, the exclusive scientific decision authority for
this bounded design audit. Read exactly the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the pushed stage commit. G33 is abandoned
and must not be reactivated. Do not authorize implementation, Git, proof
execution, nonformal exercise, formal compute, or a utility-threshold rescue.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_FORMAL_RESULT.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/project/CURRENT_WORK.md`
- `docs/report/ITERATION_31.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_formal_result_review/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md`

Audit whether an exact causal-disconnection reduction can be frozen between:

- `NATIVE6_G31_FULL`: the accepted G40 G31 branch, including its standalone
  centralized slow critic and return-loss optimizer; and
- `NATIVE6_G31_NO_SLOW`: the identical post-anchor native-six actor, log_std,
  shared two-output immediate/successor baseline module, realized-successor
  targets, per-channel normalization and direction-balanced actor update, but
  with the standalone slow-critic parameters, value loss, optimizer state and
  deployment value output removed;

while retaining identical branch-start actor/head tensors, source ledgers,
action streams, PPO exposure, actor/head optimizer state, checkpoints, reward,
lifecycle, confidence semantics and evaluation process.

## Exact treatment boundary

The only treatment may be:

- delete `centralized_slow_critic`;
- delete its return loss;
- delete its optimizer and Adam state; and
- delete its standalone value output from the retained G31 interface.

The following must remain unchanged: common fast anchor, native-six actor,
no-carry semantics, shared immediate/successor baseline module, baseline
true-current-state inputs, G31 immediate residual, G31 realized successor
residual, per-channel normalization, direction-balanced actor gradients,
external reward, G32/G34 source, action distribution, active-set aggregation
and prefix. Do not conflate removal of the standalone slow critic with removal
of true-current-state information from the shared credit-baseline module.

## Primary identification invariant

The intended result is exact equivalence, not statistical noninferiority. Define
`D_G41` as the maximum of:

- actor/log-std/shared-baseline parameter difference;
- actor/head Adam-state difference;
- pre-tanh/action/log-probability difference; and
- reward/roster/lifecycle trace difference

under one paired branch trajectory and the same actor/head update.

A removable-critic result requires:

```text
slow_critic_read_count_into_actor=0
slow_critic_read_count_into_credit_baselines=0
slow_critic_read_count_into_G31_actor_targets=0
slow_critic_read_count_into_action_or_checkpoint_selection=0
actor_and_shared_baseline_updates=bitwise_equal
actor_head_Adam_states=bitwise_equal
actions_and_reward_traces=equal_under_frozen_tolerances
```

## Claim ceilings and ordered outcomes

A pass may support only that the standalone slow critic is structurally
removable from the post-anchor NATIVE6_G31 route in G41-P0. It may not establish
that centralized true-state information is unnecessary, that the
immediate/successor baseline module can be removed, that the critic is
unnecessary for TEAM-GAE1 or another estimator, or arbitrary source/UAV
transport.

A failure may support only that the accepted G31 implementation contains a
causal or numerical slow-critic coupling preventing exact deletion. It may not
establish task-level critic necessity until that coupling is identified.

Return exactly one ordered outcome:

```text
1=INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41
2=UNREGISTERED_SLOW_CRITIC_COUPLING_G41
3=SLOW_CRITIC_EXACTLY_REMOVABLE_G41
4=NUMERICALLY_UNRESOLVED_SLOW_CRITIC_REDUCTION_G41
```

No utility threshold or extra formal evidence may substitute for the intended
exact-equivalence claim.

## Smallest evidence ceiling

First seek a zero-trajectory dependency proof. If a proof-sized execution is
required, freeze at most:

```text
one accepted G40 common-anchor state
one paired 8-episode x 48-step branch batch
real_transitions<=384
ppo_passes=2
hypothetical_transitions=0
formal_statistical_run=forbidden_unless_a_later_design_audit_changes_the_claim
wall_clock<=1200_seconds
```

The same real trajectory may feed both update paths; duplicated environment
interaction is unnecessary. File names, state-dict serialization, batching,
and test organization remain implementation-only.

## Required response sections

1. `REGISTERED_DESIGN_CONFORMANCE`
2. `DESIGN_SCIENTIFIC_DISPOSITION`
3. `IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES`
4. `CDC_PORTFOLIO_LEDGER_EDITS`
5. `DESIGN_VALID_DISPOSITION`
6. `CURRENT_SCHEDULED_ACTION_IF_CONTINUE`
7. `EXECUTABLE_DESIGN_BOUNDARY`
8. `中文简报`

Return one exact bounded design disposition. Do not implement, compute,
reinterpret G40, or select a different successor.

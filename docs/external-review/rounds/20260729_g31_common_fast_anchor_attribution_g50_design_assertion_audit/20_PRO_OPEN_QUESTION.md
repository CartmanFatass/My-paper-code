# External Pro: G50 common-fast-anchor attribution design audit

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_AUDIT
round=20260729_g31_common_fast_anchor_attribution_g50_design_assertion_audit
predecessor_formal_source_commit=8ecb01fd3ac0debf1b792e4e51293e07974d633b
```

## Authority and exact task

You are External GPT-5.6 Pro and the exclusive scientific design authority
inside this zero-compute question. Read only the paths listed in
`01_SHARED_SOURCE_MANIFEST.md` at the pushed stage commit. G33 is abandoned
and cannot be selected. Do not request permission, authorize code, or start
compute.

Audit whether the following conclusion-bearing, function-matched two-phase
comparison is scientifically identifiable and executable without changing any
unlisted semantics.

## Frozen two-phase contract to audit

```text
reference=FAST_ANCHOR_THEN_SINGLE_IMMEDIATE
null=SINGLE_IMMEDIATE_FROM_INITIALIZATION
phase_A_reference_objective=accepted_common_fast_anchor_objective
phase_A_null_objective=G49_single_immediate_objective
phase_A_updates_per_arm=100
phase_A_adam=separate_per_arm_and_discarded_at_phase_boundary
phase_boundary=identical_for_both_arms
phase_B_objective=G49_single_immediate_objective_for_both_arms
phase_B_updates_per_arm=100
phase_B_adam=fresh_empty_identically_configured_for_both_arms
primary_estimand=U_FAST_ANCHOR_THEN_SINGLE-U_SINGLE_IMMEDIATE_FROM_INITIALIZATION
materiality_and_noninferiority_margin=0.05
H=48
K_search=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
```

The two arms must retain identical pre-anchor initialization bytes, native-six
actor/log_std and actor-visible information, G32 capacity-8 fixed training
source, G34-P0 fixed/random capacity-6/8/12 evaluation source, reward, source
ledgers, member-owned action noise, PPO clipping/likelihood semantics, total
interactions, total optimizer-step exposure, phase reset, final-only checkpoint
rule and paired whole-episode confidence unit.

## Required design gates and ceilings

Freeze exact seeds, initialization identity, source/reward/RNG ledgers,
phase-boundary Adam reset, evaluation and confidence plan, result-sensitive
choices, first-match mutually exclusive outcomes, and diagnostics before any
implementation. Confirm that the comparison distinguishes fresh
single-immediate sufficiency from a finite-budget common-fast-anchor advantage.

```text
nonformal_phase_A_updates_per_arm=10
nonformal_phase_B_updates_per_arm=10
nonformal_total_real_transitions<=22272
nonformal_optimizer_steps<=80
nonformal_wall_clock<=1200_seconds
formal_replicates=3
formal_phase_A_updates_per_arm=100
formal_phase_B_updates_per_arm=100
formal_total_real_transitions<=626688
formal_optimizer_steps<=2400
formal_wall_clock<=28800_seconds
```

## Required response

Return exactly these sections once:

1. `DESIGN_ASSERTION_CONFORMANCE`
2. `FROZEN_TWO_PHASE_CONTRACT`
3. `COUNTEREXAMPLES_AND_EXCLUSIONS`
4. `RESULT_CLASSES_AND_GATES`
5. `EVIDENCE_COMPLEXITY_AND_BUDGET`
6. `IMPLEMENTATION_BOUNDARY`
7. `NEXT_BOUNDARY`
8. `中文简报`

End with exactly one disposition token: `CONTINUE`, `MISMATCH` or
`SCIENTIFIC_AMBIGUITY`. If `MISMATCH`, identify only concrete target-bound
contract defects and the smallest in-contract correction. If `CONTINUE`, state
the exact frozen design boundary and no more than one next action.

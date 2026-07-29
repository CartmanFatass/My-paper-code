# External Pro: G50 common-fast-anchor attribution correction recheck

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_CORRECTION_RECHECK
round=20260729_g31_common_fast_anchor_attribution_g50_design_assertion_correction_recheck
audit_target_round=20260729_g31_common_fast_anchor_attribution_g50_design_assertion_audit
audit_target_archival_commit=73bb301ee581a249e3fb7333f62f65b795c8acda
```

## Authority and exact task

You are External GPT-5.6 Pro and the exclusive scientific design authority
inside this zero-compute correction recheck. Read only the paths listed in
`01_SHARED_SOURCE_MANIFEST.md` at the pushed stage commit. Treat the prior G50
response as format-nonconforming because it omitted a declared section. Recheck
the same frozen two-phase contract without redesign, new evidence, code
authorization or compute.

## Frozen contract to recheck

The unchanged contract is the two-phase comparison:

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

The two arms retain identical initialization bytes, native-six actor/log_std,
actor-visible information, G32 capacity-8 training source, G34-P0 evaluation
source, reward and source ledgers, member-owned action noise, PPO semantics,
total interactions, optimizer exposure, phase reset, final-only checkpoint rule
and paired whole-episode confidence unit.

## Required correction-recheck response

Return exactly these eight headings, using the ASCII heading text verbatim:

1. `DESIGN_ASSERTION_CONFORMANCE`
2. `FROZEN_TWO_PHASE_CONTRACT`
3. `COUNTEREXAMPLES_AND_EXCLUSIONS`
4. `RESULT_CLASSES_AND_GATES`
5. `EVIDENCE_COMPLEXITY_AND_BUDGET`
6. `IMPLEMENTATION_BOUNDARY`
7. `NEXT_BOUNDARY`
8. `CHINESE_BRIEF`

Under `CHINESE_BRIEF`, provide the brief Chinese summary requested by the
original audit. End with exactly one disposition token: `CONTINUE`, `MISMATCH`
or `SCIENTIFIC_AMBIGUITY`. If `MISMATCH`, identify only concrete target-bound
contract defects and the smallest in-contract correction. If `CONTINUE`, state
the exact frozen design boundary and no more than one next action. This is a
format and target-bound correction recheck, not a request for a new design.

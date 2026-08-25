# External Pro: G50 phase-A treatment identity clarification

semantic_author=research_operations_manager
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_CLARIFICATION
round=20260729_g31_common_fast_anchor_phase_a_treatment_identity_clarification
source_round=20260729_g31_common_fast_anchor_attribution_g50_design_assertion_audit
source_disposition_round=20260729_g31_common_fast_anchor_attribution_g50_disposition_format_recheck
source_archival_commit=276b79fd0c8a10b51f75d7ff23f769a0285e9b7d

## Exact evidence allow-list

Read only the paths listed in `01_SHARED_SOURCE_MANIFEST.md` from the exact
stage commit. Ignore all earlier rounds and all unlisted repository content.

## Exact question

Freeze the sole next G50 phase-A treatment-identity boundary. State whether
`accepted_common_fast_anchor_objective` means (A) an actor/log_std assigned-
gradient law on the G49 actor graph or (B) the complete historical fast-anchor
training package. Then provide the complete code-facing contract for the chosen
interpretation:

- exact target/advantage equations, normalization and entropy law;
- complete trainable parameter/module inventory and masks;
- complete optimizer groups, hyperparameters and `optimizer.step()` count per
  PPO pass, including any auxiliary steps;
- exact phase-A to phase-B projection, reset and state-disposal rules;
- exact formal/nonformal seed bases and offsets;
- the forced-first-batch gradient identity, q_A threshold and group-liveness
  predicates relative to G49 single-immediate;
- exact nonformal/formal transition and optimizer-step ceilings.

Do not implement code, run compute, select a successor, reopen G49, or add a
new scientific objective. If the evidence does not identify one interpretation,
return `SCIENTIFIC_AMBIGUITY` and identify the smallest missing frozen field.

Return the following headings exactly, with no omission:

```text
DESIGN_ASSERTION_CONFORMANCE
phase_A_reference_interpretation=
phase_A_target_and_advantage_equations=
phase_A_trainable_inventory=
phase_A_optimizer_inventory_and_steps=
phase_A_projection_and_reset=
seed_bases_and_offsets=
forced_first_batch_gates=
transition_and_optimizer_ceilings=
disposition=<CONTINUE|MISMATCH|SCIENTIFIC_AMBIGUITY>
next_boundary=
CHINESE_BRIEF
```

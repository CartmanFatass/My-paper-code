# Continuous Roster Reactive Reduction G35

```text
document_kind=pm_code_realization
algorithm_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35
source_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0
external_pro_disposition=IDENTIFIABLE_EMPIRICAL_REACTIVE_REDUCTION_G35_DESIGN
scientific_authority=external_pro
implementation_authority=project_manager
implementation_status=pm_technically_accepted_alignment_correction
implementation_code_commit=f626dfd8a345ef670e08e601344b67e28ffb3563
superseded_implementation_code_commit=42b9f85a7820ec5f4a3a7507d3a4e644b27fbc56
formal_compute_status=complete_operational_valid_pending_external_pro_scientific_disposition
```

## Frozen contract

The scientific contract is the exact External-Pro response in
`docs/external-review/rounds/20260726_continuous_roster_reactive_reduction_g35_design_assertion_audit/21_PRO_OPEN_RAW.md`.
Its mechanical intake is the same round's
`50_MECHANICAL_INTAKE_RECORD.md`. This document records PM's mechanical code
realization and does not reinterpret that contract.

G35 compares two freshly trained, parameter-identical arms. Both retain every
registered current field, the active-fraction action prefix, the same
centralized critic, the same G31 credit graph and the same training/evaluation
exposure. The only causal difference is the nontrainable carry constant in the
shared actor cell: REC carries learned state across primitive steps and CS does
not. The claim ceiling is current-state sufficiency or a finite-budget
recurrent inductive-bias advantage; task-level recurrence necessity is
forbidden.

## PM realization boundary

- Add one matched carry policy with identical serialized keys, shapes,
  trainable masks, initialization and parameter counts across arms.
- Add one zero-initialized current-observation readout shared by both arms.
- Preserve the exact G32 fixed capacity-8 training source, G34-P0 paired
  fixed/random capacity 6/8/12 evaluation laws, lifecycle ownership, tanh
  Gaussian distribution and G31 immediate/successor credit.
- Materialize both arm trajectories before updating either arm; use fresh
  paired initialization, ledgers and member-owned action streams.
- Fail closed on the initial live-gradient audit, checkpoint/exposure
  identity, replay, lifecycle, trace recomputation, cell inventory and the
  frozen first-match table.
- Do not read, edit, stage or reactivate any abandoned G33 path.

The owned implementation surface is limited to the shared policy hook needed
by the matched cell, one G35 source module, one G35 runner, their two focused
test files, this realization record, the later commit-bound code-science index
and PM active state.

The commit-bound critical-point mapping is
`docs/research/designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_INDEX.md`.

## Evidence and complexity inventory

```text
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
nonformal_real_transitions=28032
nonformal_wall_clock_cap_seconds=1200
formal_training_transitions=460800
formal_evaluation_transitions=608256
formal_total_real_transitions=1069056
formal_optimizer_steps=3600
formal_wall_clock_cap_seconds=28800
```

The nonformal exercise must separately measure training, evaluation and
analysis time. The conservative formal projection is exactly
`1.25 * (30*T_train_nf + 48*T_eval_nf + 40*T_analysis_nf)` and must not exceed
28,800 seconds. Failure returns `NON_EXECUTABLE_EVIDENCE_DESIGN`; it is not a
scientific result and consumes no iteration.

No implementation, test or exercise may alter an arm, source, seed, margin,
confidence unit, evidence volume or terminal branch from the frozen response.
After PM technical acceptance, the next scientific boundary is the single
read-only `CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_ALIGNMENT_AUDIT`.

## PM technical acceptance

The original implementation commit
`42b9f85a7820ec5f4a3a7507d3a4e644b27fbc56` passed 14 focused tests, 79
shared-surface tests and one bounded nonformal exercise. The implementation-post
audit nevertheless returned `MISMATCH`: formal preflight trusted a favorable
`analysis_result.json` without independently validating and binding the exact
training and evaluation manifests.

The in-contract correction commit
`f626dfd8a345ef670e08e601344b67e28ffb3563` loads and validates all three
nonformal artifacts, freezes the exact 28,032-transition, 120-optimizer-step
and 33-cell inventory, recomputes the formal projection from the three
serialized stage times, binds analysis to both manifest digests and repeats
the check from the formal artifact's serialized absolute `preflight_root`.
It changes no arm, source, seed, credit rule, threshold, evidence volume,
estimand or first-match branch.

The correction passed 17 G35-focused tests and the complete 82-test
G19-through-G35 shared regression. Its single corrected bounded nonformal
exercise completed in 97.21 seconds with `operational_valid=true`; PM
independently revalidated all three artifacts and recomputed the conservative
formal projection as 3,873.24 seconds, below the 28,800-second cap. PM
technically accepts the correction. The one correction-only alignment recheck
returned `ALIGNED`; the authorized formal CPU run then completed once with an
operationally valid registered branch. Scientific interpretation remains
pending External Pro.

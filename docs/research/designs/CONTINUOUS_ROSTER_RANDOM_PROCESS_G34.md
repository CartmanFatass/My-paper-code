# Continuous Roster Random Process G34

```text
document_kind=pm_code_realization
algorithm_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34
source_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0
external_pro_disposition=IDENTIFIABLE_BOUNDED_RANDOM_PROCESS_G34_DESIGN
scientific_authority=external_pro
implementation_authority=project_manager
implementation_status=alignment_correction_candidate_pending_commit_bound_nonformal_exercise
superseded_implementation_code_commit=c2489d43d9eaa3a48a4ea18ae55f570ec3e06e63
training_change=none
optimizer_steps=0
formal_compute_status=not_started
```

## Frozen source

The scientific contract is the exact External-Pro response in
`docs/external-review/rounds/20260726_continuous_roster_random_process_g34_design_assertion_audit/21_PRO_OPEN_RAW.md`.
Its mechanical intake is
`docs/external-review/rounds/20260726_continuous_roster_random_process_g34_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`.
This document records PM's code realization only and does not reinterpret that
contract.

The implementation retains the exact usable G32 zero and final checkpoints,
the 48-step task, capacities 6/8/12, actor and critic interfaces, lifecycle
semantics, action support and reward. G34 changes no model or training path. It
adds only the registered four-event evaluation source, paired controls,
diagnostics, analysis and fail-closed evidence schema.

## Realization

- `ha_ctse_process/continuous_roster_random_process_g34.py` owns deterministic
  construction of the registered event-time tuples, balanced order/profile
  assignments, the paired G32 base ledgers, ledger-driven membership events,
  lifecycle validation, constructive evaluation and the two capacity-8
  observation interventions.
- `scripts/run_continuous_roster_random_process_g34.py` strict-loads only the
  exact usable formal G32 checkpoint source, evaluates the frozen 20-cell
  replicate inventory, validates serialized routing and episode evidence,
  reuses one hierarchical whole-episode paired bootstrap plan, applies the
  frozen first-match table and separates nonformal exercise from formal
  authority.
- The commit-bound critical-point mapping is
  `docs/research/designs/CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_CODE_SCIENCE_INDEX.md`.

The registered random branch contains one each of L, R, J and T. Time tuples
are unique within each replicate/capacity cell, lie in steps 5 through 43,
exclude multiples of four and have gaps of at least five. The allowed orders
are LRJT, LJRT and JLRT. Orders and capacity-8 profiles have 43/43/42 counts per
replicate with the 42-count category rotated, so every category totals 128
across three replicates. Fixed and random branches reuse the same base ledger,
episode identity and member-owned stochastic action stream.

## Evidence and complexity inventory

```text
H=48
intrinsic_K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
formal_replicates=3
formal_cells_per_replicate=20
formal_total_cells=60
formal_episodes_per_cell=128
formal_total_real_episode_transitions=368640
episode_exclusions=none
```

No search, candidate rollout or simulated counterfactual is present. The
commit-bound CPU nonformal exercise completed in 7.3 seconds with 20 cells,
3,840 real transitions, zero optimizer steps, unchanged checkpoint state and
`operational_valid=true`. PM initially accepted that implementation candidate;
the later alignment mismatch superseded that acceptance for formal execution.
A formal run remains prohibited until the corrected candidate completes its
bounded exercise and the required
implementation-post `CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_CODE_SCIENCE_ALIGNMENT_AUDIT`
returns aligned.

## Proof-sized code evidence

The current candidate passed:

```text
python -m pytest -q \
  tests/ha_ctse_process_continuous_roster_random_process_g34_test.py \
  tests/run_continuous_roster_random_process_g34_test.py
16 passed

python -m pytest -q \
  tests/ha_ctse_process_continuous_roster_random_process_g34_test.py \
  tests/run_continuous_roster_random_process_g34_test.py \
  tests/ha_ctse_process_runtime_capacity_continuous_roster_g32_test.py \
  tests/run_runtime_capacity_continuous_roster_g32_test.py
29 passed
```

These checks cover the registered process support and balancing, exact count
trajectories, constructive reachability, fixed/random pairing, lifecycle state,
time/reactive intervention coordinates, checkpoint immutability, exact G32
source restriction, cell and episode fail-closed validation, whole-episode
paired differences, first-match precedence, formal authority and the frozen
complexity inventory. They are code evidence, not a scientific result.

The initial bounded integration evidence is archived at
`logs/nonformal_continuous_roster_random_process_g34_cpu_20260726_c2489d4_pm1/`.
Its evaluation and analysis artifacts both bind the full implementation commit,
record `formal=false`, and terminate at
`NONFORMAL_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_EXERCISE_COMPLETE`.

## Alignment correction

The implementation-post audit returned `MISMATCH` because serialized model-cell
digests were not independently matched to the declared G32 checkpoint and
conclusion metrics were not recomputed from episode traces. The in-contract
correction upgrades the artifact schema to v2, records each 48-step reward and
roster-size trace, recomputes all conclusion-bearing summaries from those
traces, and independently strict-loads every declared replicate/kind/capacity
checkpoint for digest comparison. No process, checkpoint set, control,
diagnostic, estimand, threshold, sample count or first-match branch changes.

The correction candidate passes 18 G34-focused tests and 31 tests with the two
G32 upstream files. A new commit-bound nonformal exercise is required before PM
reaccepts it and opens the single correction-only alignment recheck.

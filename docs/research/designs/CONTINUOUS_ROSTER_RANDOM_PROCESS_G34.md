# Continuous Roster Random Process G34

```text
document_kind=pm_code_realization
algorithm_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34
source_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0
external_pro_disposition=IDENTIFIABLE_BOUNDED_RANDOM_PROCESS_G34_DESIGN
scientific_authority=external_pro
implementation_authority=project_manager
implementation_status=candidate_requires_commit_bound_nonformal_exercise
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

No search, candidate rollout or simulated counterfactual is present. A formal
run remains prohibited until the candidate commit completes one bounded CPU
nonformal exercise, PM accepts the implementation, and the required
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

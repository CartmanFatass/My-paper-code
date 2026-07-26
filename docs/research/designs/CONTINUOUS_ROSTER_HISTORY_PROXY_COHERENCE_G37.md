# Continuous Roster History-Proxy Coherence G37

```text
document_kind=pm_code_realization
algorithm_id=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0
external_pro_disposition=IDENTIFIABLE_BOUNDED_FACTORIZED_HISTORY_PROXY_COHERENCE_G37_DESIGN
scientific_authority=external_pro
implementation_authority=project_manager
implementation_status=pm_candidate_accepted_after_6_focused_and_17_G36_G37_tests_nonformal_pending
formal_compute_status=not_authorized_before_alignment_and_same_commit_preflight
training=none
```

## Frozen contract

The scientific contract is the exact External-Pro response in
`docs/external-review/rounds/20260726_continuous_roster_history_proxy_coherence_g37_design_assertion_audit/21_PRO_OPEN_RAW.md`.
G37 reads the exact formal G36 joint-donor package and exact formal G35 CS final
checkpoints. It adds only a four-column factorized donor execution.

For every active count, age, previous-action-0, previous-action-1 and time each
draw an independently selected exact G36 donor snapshot and an independently
permuted complete donor column. Each coordinate's full active-count-conditioned
column distribution is preserved. Shared snapshot identity, common row alignment,
within-row lifecycle coherence, previous-action-pair coherence and roster-level
cross-column configuration are destroyed. Accidental equality is retained.

Actor coordinates 0:6, inactive-zero rows, active mask, action prefix, critic,
source, reward, lifecycle, checkpoints, episode identities and member-owned
action streams remain unchanged. The G36 joint side is validated and read, not
rerun. A positive result concerns only cross-column coherence for the exact
checkpoints under this factorized law; it does not authorize architectural
deletion, arbitrary noise or global memorylessness.

## PM realization boundary

- Reuse the byte-identical cached `G36HistoryProxyDonorBank` with no weighting,
  filtering, clipping, deduplication or rebuilding logic.
- Use factorized seed base `10363000`, bootstrap seed `10364037` and nonformal
  offset `900000`. Address snapshot and permutation streams exactly by
  `[q, capacity, episode_id, physical_call_position, active_count, 2*k]` and
  `[q, capacity, episode_id, physical_call_position, active_count, 2*k+1]`.
- Cache by episode ID, call position and active count within one replicate/
  capacity tape. The key contains no process, mode, member identity, event,
  actual history, load/mix, reward, checkpoint output or action noise.
- Use four new cells only: `CS_FACTORIZED_FIXED_DET`,
  `CS_FACTORIZED_FIXED_STOCH`, `CS_FACTORIZED_RANDOM_DET` and
  `CS_FACTORIZED_RANDOM_STOCH`.
- Preserve the corrected G36 actor-input construction that materializes only
  source coordinates 0:6 before writing the proxy into active coordinates 6:10.
- Strict-bind and validate the exact formal G36 branch, digest, cells, traces,
  G35 artifacts and checkpoints. Recompute all reference and factorized metrics
  from serialized 48-step traces.
- Use one paired replicate/whole-episode hierarchical plan with bootstrap seed
  `10364037`; capacities are equally weighted and no row is excluded.
- Apply the frozen first-match order: invalid; source/reference failure;
  factorized sufficiency; joint coherence load-bearing; mixed/underpowered.
- Do not read, edit, stage or reactivate any abandoned G33 path.

## Evidence and complexity inventory

```text
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
training_transitions=0
optimizer_steps=0
nonformal_replicates=1
nonformal_capacities=3
nonformal_cells=12
nonformal_episodes_per_cell=8
nonformal_real_transitions=4608
nonformal_bootstrap_resamples=250
nonformal_wall_clock_cap_seconds=1200
formal_replicates=3
formal_capacities=3
formal_cells=36
formal_episodes_per_cell=128
formal_real_transitions=221184
formal_bootstrap_resamples=10000
formal_wall_clock_cap_seconds=28800
```

The formal projection is exactly
`1.25 * (48*T_evaluate_nonformal + 40*T_analyze_nonformal)`. Any bound failure
is `NON_EXECUTABLE_EVIDENCE_DESIGN` and consumes no scientific iteration.

## Acceptance sequence

PM accepts the implementation with proof-sized tests and one same-commit bounded
nonformal exercise. The implementation, tests, this record and commit-bound
critical-point index are pushed before the single read-only
`CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_CODE_SCIENCE_ALIGNMENT_AUDIT`.
Formal execution remains blocked until that audit returns `ALIGNED` and the
same-commit preflight validates under the dedicated G37 token.

# G36 Prelaunch Evidence Note

```text
document_kind=pm_prelaunch_runtime_evidence
algorithm_id=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0
implementation_code_commit=e96f0be154afcf778780bad6266458e211b4b047
alignment_disposition=MISMATCH
repair_implementation_code_commit=pending_git_commit_containing_no_read_evaluator_correction
prior_nonformal_preflight_status=superseded_by_source_change
pm_technical_acceptance=accepted
scientific_interpretation=none
formal_compute_started=false
```

## Proof and integration evidence

PM corrected two fail-closed realization defects before integration: nonformal
registered arrays now use exactly one replicate and the first eight inherited
episodes, and the actor transform does not validate or copy active-row target
coordinates 6:10 before replacement. Ten focused G36 tests and the 58-test
G32/G34/G35/G36 aggregate regression passed on the registered CPU interpreter.
PM also strict-loaded the accepted formal G35 package and reproduced its exact
source commit, terminal branch and CS access predicate.

The registered Experiment Operator then executed exactly one bounded
nonformal CPU exercise without retry:

```text
run_root=logs/nonformal_continuous_roster_history_proxy_free_cs_g36_cpu_20260726_e96f0be_r1
source_commit=e96f0be154afcf778780bad6266458e211b4b047
formal=false
authorization_token=absent
preflight_root=absent
exit_code=0
evaluation_wall_time_seconds=29.87909119999954
analysis_wall_time_seconds=16.797078699999474
replicates=1
capacities=3
cells=12
episodes_per_cell=8
evaluation_transitions=4608
optimizer_steps=0
bootstrap_resamples=250
operational_valid=true
operational_errors=[]
branch=NONFORMAL_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_COMPLETE
```

PM independently reread both terminal JSON artifacts without rerunning the
experiment. The registered validator returned an empty error list after
strictly revalidating the G35 manifests, analysis and CS checkpoints; the exact
source and absolute G35 root; donor active-count support; all twelve cell keys;
actor-only zero-read counters; zero checkpoint updates and before/after state
identity; per-episode proxy-tape reuse; exact member-owned action-noise digests;
episode identities, process signatures and 48-step traces; and every serialized
utility, event-window and process-segment summary.

```text
evaluation_manifest_sha256=3184bb6257aabf691e62fe3f925ceabb04ef08abf02dc9740969d93eea818fd6
```

## Formal capacity projection

The frozen projection was independently recomputed from the two serialized
stage times:

```text
T_projected_formal=1.25*(48*T_evaluate_nonformal+40*T_analyze_nonformal)
T_projected_formal_seconds=1847.8693610000664
T_projected_formal_minutes=30.79782268333444
T_projected_formal_hours=0.5132970447222407
formal_wall_clock_cap_seconds=28800
prelaunch_capacity_status=EXECUTABLE_WITHIN_BOUND
```

The possible formal inventory remains 36 intervention cells, 4,608 episodes,
221,184 real transitions, zero optimizer steps and 10,000 paired hierarchical
bootstrap resamples. `H=48`, `K_search=0`, hypothetical transitions are zero,
and no nested rollout or replanning exists.

This note authorizes no formal run. The exact implementation and commit-bound
code-science index must first return `ALIGNED` from the single registered
zero-compute G36 code-science audit.

## Alignment correction

The first audit found that `evaluate_g36_history_proxy` materialized the full
ten-coordinate source observation before the already-correct transform
overwrote coordinates 6:10. The smallest correction constructs a fresh zeroed
actor tensor from source prefix `:6` only and writes the proxy bundle directly;
read counters are returned from this exercised construction path. A new
end-to-end evaluator guard ran all 48 physical steps and would fail if any
protected source coordinate reached the pre-substitution actor buffer. Eleven
focused tests and the 59-test G32/G34/G35/G36 regression passed. Because the
source commit changed, the earlier operationally valid preflight above cannot
authorize formal compute and must be replaced by one bounded exercise from the
exact repair commit before correction recheck.

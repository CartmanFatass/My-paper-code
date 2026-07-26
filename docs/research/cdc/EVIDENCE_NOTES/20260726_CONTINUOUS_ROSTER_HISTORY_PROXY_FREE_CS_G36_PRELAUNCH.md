# G36 Prelaunch Evidence Note

```text
document_kind=pm_prelaunch_runtime_evidence
algorithm_id=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0
implementation_code_commit=8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04
superseded_implementation_code_commit=e96f0be154afcf778780bad6266458e211b4b047
original_alignment_disposition=MISMATCH
alignment_correction_recheck_disposition=ALIGNED
repair_implementation_code_commit=8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04
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

The registered Experiment Operator then completed exactly one replacement
preflight from the repair commit, without retry:

```text
run_root=logs/nonformal_continuous_roster_history_proxy_free_cs_g36_cpu_20260726_8f1cd60_r1
source_commit=8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04
formal=false
exit_code=0
evaluation_wall_time_seconds=20.494850800001586
analysis_wall_time_seconds=17.53727549999894
evaluation_transitions=4608
optimizer_steps=0
operational_valid=true
operational_errors=[]
branch=NONFORMAL_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_COMPLETE
evaluation_manifest_sha256=8f7397f384a2e0d97fa8842f8555f9530eb1831276882def07f74619d4498223
formal_projection_seconds=2106.5548230000422
formal_projection_executable=true
```

PM independently reran the registered artifact validator and received an empty
error list, then reproduced the exact source commit, inventory, zero optimizer
count, terminal branch, manifest digest and projection arithmetic. This note
still authorizes no formal compute; the exact correction must first return
`ALIGNED` from the bounded correction recheck.

The exact zero-compute correction recheck subsequently returned
`AUDIT_DISPOSITION=ALIGNED`. Together with the active standing CPU grant, this
closes the registered prelaunch boundary for exactly one formal G36 evaluation
from repair commit `8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04` and the replacement
preflight above. It authorizes no retry or successor interpretation.

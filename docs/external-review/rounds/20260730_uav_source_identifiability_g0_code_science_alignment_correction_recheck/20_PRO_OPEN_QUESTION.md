# External Pro open question: UAV G0 code-science alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=read_only_target_bound_correction_only
compute_budget=zero
audit_target_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43
implementation_code_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43
original_audit_target_commit=ae1e01c64643b816fd15534fbfd46d16d3bf2f17
design_contract_stage_commit=8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc
readiness_contract=UAV_G0_READINESS_PERFORMANCE_CONTRACT_V2
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded correction recheck. Use the connected GitHub repository connector
for `https://github.com/CartmanFatass/My-paper-code.git`, branch `aggressive`,
and read only the allow-list in `01_SHARED_SOURCE_MANIFEST.md` at the exact
target commit. Do not use a local working tree, runtime logs, unlisted files,
or compute. Do not activate Answer now.

The prior audit reported this exact mismatch at `ae1e01c64643b816fd15534fbfd46d16d3bf2f17`:
`ha_ctse_process/uav_source_identifiability_g0.py::run_g0_episode` marked an
Oracle behavioral candidate and called `env.step_dense(actions)` without
`oracle_ownership`, `oracle_pre_action_context`, or
`oracle_common_transducer_evidence`; the real S7-S1 guard therefore rejected
Oracle EVENT and NO_EVENT before EpisodeRunEvidence could be produced.

At the exact target `9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43`, check only whether
the smallest in-contract repair is present and preserves the frozen semantics:

1. In the `Control.ORACLE` production branch, a pre-action context is created
   before target selection, target-owned internal positions/targets/active mask
   are reconstructed, common-transducer evidence is freshly recomputed for the
   exact raw action, and all three evidence objects are passed to `step_dense`.
   The storage/internal permutation check must remain explicit.
2. The repair must apply to both EVENT and NO_EVENT without introducing a new
   controller, oracle heuristic, target rule, metric, seed, or result-bearing
   path. The existing accepted tracker, unchanged S7-S1 guard, ownership map,
   tie semantics and frozen R=273/R=NONE replay meanings remain authoritative.
3. The indexed production regression must exercise both Oracle EVENT and
   NO_EVENT, verify branch-aware certificates and episode-0 `R=273`/`R=NONE`,
   and keep lifecycle, tracker, ownership and qualification counters zero.
4. Any readiness or artifact changes must remain mechanical only: no scientific
   training/evaluation/checkpoint path is opened and no frozen G0 field changes.

Return exactly one disposition and no Chinese summary:

- `AUDIT_DISPOSITION=ALIGNED` if the target bytes close the prior mismatch and
  all four points conform.
- `AUDIT_DISPOSITION=MISMATCH` only with an exact target-bound conflicting
  path/symbol/behavior and the smallest correction; do not propose redesign or
  compute.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only if a previously unstated,
  result-changing scientific choice prevents this correction recheck.

Do not reopen the original G0 design, merge G51, or request additional
evidence beyond the allow-list. Stop after this single scoped disposition.

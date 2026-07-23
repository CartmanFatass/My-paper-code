# HA-CTSE Current Work

Last updated: 2026-07-23

This file records active state only. Durable authority is in `AGENTS.md` and
`.agents/roles/*.md`.

## Active execution surface

- Project Manager task `019f8a2e-ed73-7a02-9bb9-4a57b2054cf3` is the sole
  persistent project task and owns workflow, science reconciliation,
  implementation acceptance, Git, external-review transport, experiment
  orchestration, evidence intake, and successor selection.
- `hmasd-experiment-operator` is a registered nonpersistent native child fixed
  to `gpt-5.6-luna` with `low` reasoning. It is spawned for one authorized run,
  remains silent during execution, and returns exactly one `COMPLETE` or
  `ERROR` final payload.
- No Controller, persistent Monitor, dispatcher, monitor Skill, callback route,
  or experiment heartbeat is active.
- External GPT-5.6 Pro remains question-scoped scientific authority reached by
  Project Manager direct transport with `$hmasd-review-round`.

## Active boundary

```text
last_completed_assignment_id=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION
active_assignment_id=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_ITERATION_2_OPERATIONAL_REPAIR
accepted_source_commit=3d1d92711763034bf7f022b812f3f3431bb59776
next_boundary=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_ITERATION_2_CLEAN_R2
iterations_remaining=4
conclusion_bearing_iterations_consumed_by_failed_r1=0
autonomous_research_grant=ACTIVE
grant_scope=remaining_four_conclusion_bearing_iterations
intermediate_authorization_prompts=forbidden
implementation_status=authorized
nonformal_compute_status=authorized
formal_compute_status=authorized_cpu_only_under_frozen_evidence_contract
git_integration_status=project_manager_direct_authorized
external_review_transport_status=project_manager_direct_authorized_when_selected
experiment_operator_status=registered_pm_accepted
formal_evidence_contract_status=PM_FROZEN
formal_evidence_contract=docs/research/designs/ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1.md
formal_implementation_status=PM_ACCEPTED_PRELAUNCH
formal_run_status=r1_operational_error_no_valid_analysis
formal_r1_artifact=logs/formal_access_positive_ehc_g1_cpu_20260723_3d1d927_r1
formal_r1_terminal_phase=TRAIN
formal_r1_last_progress=replicate_1_arm_OR_update_90
formal_r1_error=PermissionError_WinError_5_atomic_progress_replace
formal_r1_evaluate_status=not_launched
formal_r1_analyze_status=not_launched
formal_r1_scientific_disposition=none
operational_repair_status=PM_ACCEPTED
operational_repair=bounded_permission_retry_plus_silent_foreground_operator
restart_policy=clean_run_root_after_repair_commit_no_cross_commit_resume
workflow_hash_validation=disabled
backward_compatibility=not_required
```

The first formal G1 run has no valid scientific result. Its same-command
foreground resume exited while atomically replacing `progress.json` under a
Windows/OneDrive sharing lock:

```text
PermissionError: [WinError 5] Access is denied:
'logs\\formal_access_positive_ehc_g1_cpu_20260723_3d1d927_r1\\.progress.json.35684.tmp'
-> 'logs\\formal_access_positive_ehc_g1_cpu_20260723_3d1d927_r1\\progress.json'
```

Training stopped at replicate 1, OR update 90. Evaluation and analysis were not
started. The run consumed no conclusion-bearing iteration and must remain as
operationally invalid evidence. After the atomic-write and operator topology
package is accepted and committed, iteration 2 restarts from a fresh run root
under that new source commit; the old checkpoint is not resumed across commits.

## Accepted scientific state

- `EVENT_HELD_COMMITMENT_LINK_G0` is permanently closed as
  `NO_ACCESS_THIS_BENCHMARK`; it may not be rerun, renamed, modified, or rescued.
- The G1 formal contract at
  `docs/research/designs/ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1.md` is frozen.
- The bounded prelaunch artifact
  `logs/nonformal_access_positive_ehc_g1_prelaunch_20260723_pm2` validated the
  learned G1 execution path and was correctly rejected as nonformal.
- The r1 operational error changes no estimand, source, threshold, budget,
  branch, or scientific result gate.
- Four conclusion-bearing iterations remain.

## Runtime and protected semantics

```text
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
torch=2.7.0+cpu
torch_threads=1
backend=cpu
```

There is no CUDA fallback, backend mixing, cross-backend resume, or CPU/CUDA
equivalence requirement. Preserve the closed G0 source; OR/DUM/EHC;
`primitive_logits = base_logits + W_z(m*z)`; primary
`G = U_EHC - U_DUM`; anonymous membership/lifecycle semantics; reward,
observation, probability factorization, gradients/detach, clocks, RNG, replay,
checkpoint meaning, seeds, budgets, thresholds, bootstrap, causal gates, and
first-match result precedence.

## Concurrency

```text
concurrency_policy=file_ownership_only
global_write_lease=disabled
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
active_file_writers=none
```

Children do not run Git; Project Manager directly commits and pushes the
accepted exact path set. No workflow hash or callback receipt is required.

## Pointers

- `AGENTS.md` and `.agents/roles/PROJECT_MANAGER.md` — project authority.
- `.agents/roles/EXPERIMENT_OPERATOR.md` — silent single-run child contract.
- `.codex/agents/hmasd-experiment-operator.toml` — fixed Luna-low profile.
- `docs/project/IMPLEMENTATION_PLAN.md` — active executable plan.
- `docs/research/designs/ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1.md` — frozen
  formal evidence contract.

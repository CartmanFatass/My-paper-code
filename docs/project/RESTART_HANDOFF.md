# Codex restart handoff

```text
document_kind=user_requested_restart_snapshot
write_trigger=explicit_user_request_only
automatic_create_or_update=forbidden
date=2026-07-26
status=PAUSED_BY_USER_FOR_SESSION_RESTART
active_role=research_operations_manager
controller_role=none
branch=aggressive
implementation_base_head=8478935bdd48e7f41b050671afce788b91d68b89
implementation_base_remote_status=origin_aggressive_equal
iterations_remaining=12
formal_compute=none_g35
external_review=none_active
live_child_work=none_all_registered_children_terminal
```

## Restart role resolution

The replacement operational task is Research Operations Manager. It loads
`AGENTS.md`, `docs/project/CURRENT_WORK.md` and
`.agents/roles/RESEARCH_OPERATIONS_MANAGER.md`. Code work is sent to the fixed
Code Project Manager, which loads its exact assignment and
`.agents/roles/CODE_PROJECT_MANAGER.md` but never `CURRENT_WORK.md`. Do not
change workflow design or any Workflow Design Manager-owned path.

Every cross-task send must resolve the target task's live model and reasoning
effort immediately before sending and pass both explicitly. Research Operations
Manager remains task `019f9c6a-9401-7ae0-ace5-dd827dccba2b`; Code Project
Manager remains task `019f9e4f-f4d0-7fe0-b214-c47fd034e84d`. Model and effort
are live task settings and are not stored here. Experiment work uses one registered
nonpersistent `hmasd-experiment-operator` at `gpt-5.6-luna/low` for each exact
authorized run. Re-resolve these identities rather than silently relying on
this snapshot.

## Active G35 boundary

The G35 code-science alignment audit naturally completed after one recovery
monitor with one original submission and no recovery submission. Its exact raw
result is `AUDIT_DISPOSITION=MISMATCH`; this is an engineering authorization
boundary finding, not a scientific-design change. The raw response, mechanical
intake and PM state were committed and pushed as:

```text
alignment_mismatch_archive_commit=8478935bdd48e7f41b050671afce788b91d68b89
alignment_stage_commit=b0fc628731f453749761330cdfed3a257d0d7971
audit_target_commit=49b3ba9399b056bd601863d6b0f2305c222f1f66
original_implementation_code_commit=42b9f85a7820ec5f4a3a7507d3a4e644b27fbc56
raw=docs/external-review/rounds/20260726_continuous_roster_reactive_reduction_g35_code_science_alignment_audit/21_PRO_OPEN_RAW.md
intake=docs/external-review/rounds/20260726_continuous_roster_reactive_reduction_g35_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md
formal_status=PROHIBITED_UNTIL_CORRECTION_ONLY_RECHECK_ALIGNED
```

The accepted smallest correction is exact and changes no arm, source, seed,
credit rule, threshold, evidence volume, estimand or first-match branch:

1. Formal preflight must load `train_manifest.json`,
   `evaluation_manifest.json` and `analysis_result.json`.
2. It must run the existing training and evaluation validators, require exact
   nonformal configuration, and close one replicate, two arms, 10 fast plus 10
   return-to-go updates per arm, 33 cells, 28,032 real transitions and 120
   optimizer steps.
3. It must recompute the formal projection from the three serialized stage
   times and bind the analysis result to the validated train/evaluation files.
4. Formal artifact validation must repeat this check through the serialized
   absolute `preflight_root`, so later path or manifest tampering routes formal
   analysis to the invalid branch.

## Uncommitted accepted-scope implementation

Only these G35 paths contain the correction or its commit-bound index and are
owned by Code Project Manager:

- `scripts/run_continuous_roster_reactive_reduction_g35.py`
- `tests/run_continuous_roster_reactive_reduction_g35_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_INDEX.md`

The runner currently adds artifact digests, finite nonnegative stage-time
validation, full three-artifact preflight validation, exact frozen inventory
checks, recomputed projection equality, analysis-to-manifest digest binding and
formal artifact revalidation from the serialized preflight root. The tests add
favorable-summary-only rejection, wrong-inventory rejection, digest assertions
and a focused proof that formal artifact validation rechecks the serialized
preflight.

Focused validation completed before the pause:

```text
focused_command=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/ha_ctse_process_continuous_roster_reactive_reduction_g35_test.py tests/run_continuous_roster_reactive_reduction_g35_test.py
focused_result=17_passed
focused_wall_time_seconds=35.50
```

The 82-test shared G19-through-G35 regression was started, then explicitly
terminated immediately when the user requested this pause. It produced no
terminal result and must be rerun from the beginning; do not record it as a
failure or a pass.

```text
shared_regression_status=INTERRUPTED_BY_USER_NO_RESULT
```

Use this exact shared-suite path set on resume:

```text
tests/ha_ctse_process_anchored_residual_g19_test.py
tests/ha_ctse_process_direction_balanced_full_actor_g30_test.py
tests/ha_ctse_process_return_to_go_direction_balanced_full_actor_g31_test.py
tests/run_return_to_go_direction_balanced_full_actor_g31_test.py
tests/ha_ctse_process_runtime_capacity_continuous_roster_g32_test.py
tests/run_runtime_capacity_continuous_roster_g32_test.py
tests/ha_ctse_process_continuous_roster_random_process_g34_test.py
tests/run_continuous_roster_random_process_g34_test.py
tests/ha_ctse_process_continuous_roster_reactive_reduction_g35_test.py
tests/run_continuous_roster_reactive_reduction_g35_test.py
```

## Preserved abandoned G33 boundary

The following unrelated dirty paths are abandoned G33 work. Do not inspect,
edit, execute, stage or commit them:

- `ha_ctse_process/uav_localized_demand_burst_g33.py`
- `tests/ha_ctse_process_uav_localized_demand_burst_g33_test.py`
- `scripts/run_uav_localized_demand_burst_g33.py`
- `tests/run_uav_localized_demand_burst_g33_test.py`

G33 remains user-abandoned, carries zero iteration cost and cannot be
reactivated without a new direct user instruction.

## Exact resume sequence

1. Research Operations Manager sends one exact G35 correction assignment and
   the three code-owned paths above to Code Project Manager.
2. Code Project Manager inspects only the G35 diff, reruns the complete 82-test
   shared suite and relevant syntax compilation, repairs only the frozen
   correction boundary if required, and updates the code-science index.
3. Code Project Manager stages exactly the three G35 code/index paths, checks the
   cached path set and `git diff --cached --check`, commits and pushes
   `aggressive`, then returns `CODE_ACCEPTED` with commit, paths and verification.
4. Research Operations Manager dispatches exactly one fresh bounded nonformal G35 exercise through a newly
   registered Luna/low Experiment Operator. Use a new run root and the corrected
   code commit. The old run at
   `logs/nonformal_continuous_roster_reactive_reduction_g35_cpu_20260726_42b9f85_pm1`
   is operational evidence for the old code but is not an admissible preflight
   for the corrected digest-binding contract.
5. Research Operations Manager must mechanically reread all three new artifacts, independently validate
   exact identity, inventory, checkpoint/exposure/lifecycle closure, digest
   binding and recomputed projection without rerunning the experiment.
6. Research Operations Manager updates the G35 prelaunch note, design
   implementation status and `CURRENT_WORK.md`, then stages a correction-only
   alignment recheck package bound to the corrected implementation and accepted
   target commit.
7. Research Operations Manager submits that exact pushed package directly in
   its registered browser transport mode. One correction-only submission is
   allowed; do not reopen the design or request a full audit.
8. Start no formal compute unless the correction-only result is exactly
   `ALIGNED`. Then use the corrected nonformal preflight root and frozen formal
   token through one registered Luna/low Experiment Operator.

No experiment, review submission, formal run, Git integration of the G35 code
correction, or successor-science work is active at this pause.

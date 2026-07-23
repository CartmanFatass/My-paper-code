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
last_completed_assignment_id=CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_TRAINABLE_CONTRACT_DEFINITION
active_assignment_id=CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_TRAINABLE_IMPLEMENTATION
accepted_source_commit=de9a315b4969ee6920be08a3d911d559fe362f03
implementation_base_commit=f54ffb643beb6d1acc925cde8e424533dfef5080
next_boundary=CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_TRAINABLE_IMPLEMENTATION
iterations_remaining=3
conclusion_bearing_iterations_consumed_by_failed_r1=0
conclusion_bearing_iterations_consumed_by_valid_r2=1
autonomous_research_grant=ACTIVE
grant_scope=remaining_three_conclusion_bearing_iterations
intermediate_authorization_prompts=forbidden
implementation_status=G2_TRAINABLE_AUTHORIZED
nonformal_compute_status=authorized
formal_compute_authority=standing_user_grant_cpu_only
formal_compute_status=not_launchable_until_g2_implementation_acceptance
git_integration_status=project_manager_direct_authorized
external_review_transport_status=project_manager_direct_authorized_when_selected
experiment_operator_status=registered_available_idle
experiment_operator_last_terminal=COMPLETE
experiment_operator_fallback=forbidden
closed_g1_evidence_contract=docs/research/designs/ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1.md
formal_evidence_contract_status=G2_PM_FROZEN_IMPLEMENTATION_PENDING
formal_evidence_contract=docs/research/designs/CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2.md
formal_implementation_status=G2_PENDING
formal_run_status=g2_not_launched_contract_frozen_implementation_pending
formal_r2_artifact=logs/formal_access_positive_ehc_g1_cpu_20260723_de9a315_r2
formal_r2_result=ORDINARY_EXPLANATION_G1
formal_r2_operational_valid=true
formal_r2_source_identifiable=true
formal_r2_max_arm_utility_ci95=[0.9293551393,0.9420615267]
formal_r2_gain_ucb=0.0026465277
formal_r2_scientific_disposition=closed_no_rerun_tuning_rename_or_rescue
formal_r1_artifact=logs/formal_access_positive_ehc_g1_cpu_20260723_3d1d927_r1
formal_r1_status=operationally_invalid_no_scientific_disposition
g2_information_gate_status=PASS_HANDOFF_INFORMATION_GATE_G2
g2_information_gate_artifact=logs/nonformal_cross_lifecycle_handoff_g2_20260723_pm2/result.json
g2_information_gate_iteration_cost=0
g2_primary_comparator=TEAM_REC
g2_primary_estimand=U_EHC_minus_U_TEAM_REC
g2_link_estimand=U_EHC_minus_U_DUM
g2_access_floor=0.80
g2_gain_margin=0.10
next_action_class=implementation_and_bounded_nonformal_acceptance
next_action_evidence=docs/research/designs/CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2.md
workflow_hash_validation=disabled
backward_compatibility=not_required
```

The clean r2 formal pipeline completed train, evaluate and analyze under the
registered silent operator. Project Manager validation closed all 15 final
checkpoints, 60 evaluation files, source controls and causal-audit evidence and
independently reproduced `ORDINARY_EXPLANATION_G1` from the frozen first-match
selector. The source is accessible, but both EHC gain upper bounds are
`0.0026465277 <= 0.10`. The result consumes conclusion-bearing iteration 2 and
leaves three iterations.

The exact G1 pair is permanently closed. The older r1 directory remains an
operationally invalid, non-conclusion-bearing record; it is never resumed or
combined with r2.

## Accepted scientific state

- `EVENT_HELD_COMMITMENT_LINK_G0` is permanently closed as
  `NO_ACCESS_THIS_BENCHMARK`; it may not be rerun, renamed, modified, or rescued.
- The G1 formal contract at
  `docs/research/designs/ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1.md` is frozen.
- The bounded prelaunch artifact
  `logs/nonformal_access_positive_ehc_g1_prelaunch_20260723_pm2` validated the
  learned G1 execution path and was correctly rejected as nonformal.
- G1 is valid `ORDINARY_EXPLANATION_G1`: ordinary per-lifecycle recurrence is
  sufficient and the commitment link is non-load-bearing for this exact source.
- C-EHC remains live only where task-relevant state must survive an anonymous
  lifecycle handoff after the creator's recurrent state is unavailable.
- The next zero-compute boundary defines that information-ownership separation;
  the bounded gate passed without launching iteration 3.
- The G2 gate proves fresh per-member recurrence is information-limited to 0.5,
  but TEAM_REC and EHC both constructively attain 1.0. TEAM_REC is therefore the
  mandatory strongest comparator for any trainable G2 claim.
- The trainable contract is now frozen with TEAM_REC as primary comparator and EHC-minus-
  TEAM_REC as primary gain.
- G2 implementation and a bounded nonformal exercise are active. Formal
  iteration 3 is not launchable until Project Manager accepts and integrates
  that exact implementation.
- Three conclusion-bearing iterations remain.

## Runtime and protected semantics

```text
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
torch=2.7.0+cpu
torch_threads=1
backend=cpu
```

There is no CUDA fallback, backend mixing, cross-backend resume, or CPU/CUDA
equivalence requirement. Preserve every closed G0/G1 source, estimand and result.
The active G2 contract uses TEAM_REC/DUM/EHC, retains
`primitive_logits = base_logits + W_z(m*z)` for EHC, and freezes primary
`G_team = U_EHC - U_TEAM_REC` plus link control
`G_link = U_EHC - U_DUM`. Preserve its anonymous membership/lifecycle semantics,
reward, observation, probability factorization, gradients/detach, clocks, RNG,
replay, checkpoint meaning, seeds, budgets, thresholds, bootstrap, causal gates,
and first-match result precedence.

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

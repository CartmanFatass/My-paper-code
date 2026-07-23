# HA-CTSE Current Work

Last updated: 2026-07-23

This file records active state only. Durable authority is defined by
`AGENTS.md` and `.agents/roles/*.md`.

## Active roles

- Project Manager: task `019f8a2e-ed73-7a02-9bb9-4a57b2054cf3`, ACTIVE,
  primary research/workflow/algorithm/engineering authority.
- Controller: task `019f8995-7550-7c82-8f31-ad08a3d381d4`, ACTIVE mechanical operator
  for exact routing, Git, external-review transport, authorized run commands,
  artifact collection, and direct bounded monitoring.
- No persistent Experiment Monitor task is active. Controller performs bounded
  monitoring directly with `$hmasd-experiment-monitor` after a run is authorized.
- External GPT-5.6 Pro is not a persistent task. It is question-scoped external
  scientific authority reached through Controller-direct external-Pro transport
  performed mechanically.

Role identity and contracts are resolved from
`.agents/skills/hmasd-dispatch-task/references/session-roles.json`; this active
state file declares no independent authority.

## Active boundary

```text
last_completed_assignment_id=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1
active_assignment_id=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION
source_boundary=local_and_remote_aggressive_tip
accepted_base_source_commit=688d95e32b86f4ee4151b4b12ddbcaf14beee18e
derivation_source_commit=3b5e86a6ef4e8731a37232df3f1828affb0d62fc
derivation_integration_commit=688d95e32b86f4ee4151b4b12ddbcaf14beee18e
accepted_reconciliation=docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned/30_PM_CODE_SIDE_RECONCILIATION.md
iterations_remaining=4
autonomous_research_grant=ACTIVE
grant_scope=remaining_four_conclusion_bearing_iterations
intermediate_authorization_prompts=forbidden
implementation_status=authorized
nonformal_compute_status=authorized
formal_compute_status=authorized_cpu_only_under_frozen_evidence_contract
git_integration_status=authorized_for_pm_accepted_packages
external_review_transport_status=authorized_when_pm_selected
monitoring_status=authorized_for_active_runs
grant_stop_conditions=iterations_exhausted|user_pause|unrecoverable_blocker|scope_outside_hmasd_mission
derivation_status=complete
prototype_status=complete_valid_nonformal
next_boundary=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION
prototype_authorization_status=authorized_under_autonomous_grant
prototype_design_status=PM_ACCEPTED
prototype_design_activation=integrated_37d6556a3a4b5bf4ed70a15834e946005354f91f
prototype_execution_kind=bounded_nonformal_measurement_prototype
prototype_conclusion_bearing_iterations_consumed=0
prototype_artifact=logs/nonformal_ehc_sequence_mediation_g1_20260723_pm3
prototype_measurement_disposition=measurement_path_valid_recurrence_remains_sufficient
formal_evidence_contract_status=not_yet_frozen
controller_integration_receipt_status=complete_1a4fb630d8c3075380cc3c6562199ee3ea28e9de
workflow_hash_validation=disabled
code_handoff_identity=git_commit_and_exact_path_set
callback_contract_activation=on_integration_commit
callback_receipt_requires_followup_commit=false
```

Project Manager completed the zero-compute CDC action
`EHC_MEASUREMENT_COUNTEREXAMPLE_DERIVATION`, recorded at
`docs/research/cdc/EVIDENCE_NOTES/20260722_EHC_MEASUREMENT_COUNTEREXAMPLES.md`.
It formalized:

- `CE-RANDOM-USE`;
- `CE-EXOGENOUS-LIFETIME`;
- `CE-LOGIT-WITHOUT-BEHAVIOR`;
- the necessary policy-dependent persistence, sequence-level intervention,
  natural mediation, simpler-explanation resistance, and held-out robustness
  conditions.

The action recorded the smallest measurement/conjecture correction, retained
lemmas and portfolio delta. It selected one bounded diagnostic prototype as the
cheapest next separating action. On 2026-07-23 the user activated a continuing
autonomous grant for the remaining four-iteration research chain. Project
Manager may now advance the selected prototype through design, implementation,
bounded nonformal diagnostics, frozen-contract formal CPU runs, needed external
review, mechanical Git integration, monitoring and successor selection without
intermediate authorization prompts.

The grant does not relax frozen scientific semantics or let Controller choose
research actions. Project Manager remains responsible for freezing each
evidence contract before a conclusion-bearing run and for stopping when the
iteration chain is exhausted, the user pauses it, an unrecoverable blocker
remains, or the next action leaves the HMASD mission.

Project Manager then completed the bounded nonformal prototype recorded at
`docs/research/cdc/EVIDENCE_NOTES/20260723_EHC_SEQUENCE_MEDIATION_PROTOTYPE_G1.md`.
Its validated 192-cell CPU artifact distinguishes the random-use,
exogenous-lifetime and logit-without-behavior nulls with the corrected
sequence-mediation tuple. The matched recurrent control reaches the same hidden
correctness and natural utility as the mechanism control, so recurrence remains
a sufficient ordinary capability explanation and the prototype carries no
adoption or superiority meaning.

The smallest next boundary is the trainable G1 formal executable definition.
It freezes the access-first result contract and ordinary-explanation outcome,
then implements focused prelaunch evidence. No formal run starts before that
contract is frozen. The derivation and prototype each consume no conclusion-bearing iteration; four conclusion-bearing iterations remain.

## Accepted evidence state

- `EVENT_HELD_COMMITMENT_LINK_G0` is permanently closed as
  `NO_ACCESS_THIS_BENCHMARK`. It may not be rerun, renamed, modified, or rescued.
- The formal CPU run completed operationally and its first-match branch is
  accepted. CPU/CUDA comparison is not an evidence requirement.
- The external-Pro result review is complete and retained the four live
  explanations: shared credit/optimization failure, shared base-policy
  insufficiency, useful EHC masked by no access, and link-null/task-mechanism
  mismatch.
- The PM-owned G1 raw, focused raw, mechanical intake records, and accepted
  code-side reconciliation are archived under
  `docs/external-review/rounds/20260722_ehc_g1_*_pm_owned/`.
- The accepted reconciliation classified the remaining source-field detail as
  algorithm semantics, deferred evidence contract, PM-owned engineering, or
  premature ontology. It selected derivation before implementation.

Lower-precedence `G`, K-bin, `I_TV`, and `C_total` diagnostics never relabel the
closed G0 result. `BATTERY_CONTRACT_RECONCILED` remains in force.

## Runtime condition

The registered runtime is CPU only:

```text
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
torch=2.7.0+cpu
torch_threads=1
backend=cpu
```

There is no CUDA fallback, backend mixing, cross-backend resume, or required
CPU/CUDA equivalence comparison. Under the active autonomous grant, Project
Manager may authorize the Controller to execute a formal CPU run only after its
evidence contract is frozen. No additional intermediate user prompt is needed.

## Frozen scientific semantics

Until a later accepted scientific boundary explicitly changes them, preserve:

- the closed G0 source and its registered first-match result;
- OR/DUM/EHC and `primitive_logits = base_logits + W_z(m*z)`;
- primary `G = U_EHC - U_DUM`;
- anonymous membership and lifecycle semantics;
- reward, observation, probability factorization, gradients/detach, clocks,
  RNG ownership/draw order, replay, checkpoint meaning, seeds, budgets,
  thresholds, bootstrap, causal gates, and result precedence;
- the unchanged behavioral battery and intrinsic-reward environment agnosticism.

Evidence gates answer local measurement questions. They are not global
admission gates for the algorithm family.

## Concurrency and current file ownership

```text
concurrency_policy=file_ownership_only
global_write_lease=disabled
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
```

All parallel child scopes and Project Manager integration are complete:

```text
active_file_writers=none
package_status=PROTOTYPE_IMPLEMENTATION_INTEGRATED_1a4fb630d8c3075380cc3c6562199ee3ea28e9de
```

The derivation package was mechanically integrated and pushed as
`688d95e32b86f4ee4151b4b12ddbcaf14beee18e`. Controller did not send the
required completion receipt to Project Manager; the user relayed the exact
receipt and woke the workflow. The callback-contract repair owns only the files
declared in its terminal Project Manager payload. The repaired callback contract
becomes active in the commit that integrates it. Its subsequent mechanical
receipt is runtime coordination evidence and does not require a follow-up state
commit, avoiding a recursive commit/receipt chain.

Different ownership sets may proceed concurrently. No repository-wide write
lease is active. Controller must wait only for a file it intends to stage while
that exact file still has an active writer.

## Pointers

- `AGENTS.md` — global role constitution and workflow.
- `.agents/roles/` — normative role contracts.
- `docs/project/ALGORITHM_PRINCIPLES.md` — scientific constraints.
- `docs/project/AGENT_CONTEXT.md` — execution environment and lightweight task
  practices.
- `docs/external-review/rounds/20260722_ehc_formal_result_review/` — accepted G0
  formal-result review.
- `docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned/`
  — focused Pro raw, mechanical intake, and PM reconciliation.
- `docs/research/cdc/CONJECTURES.md` and `docs/research/cdc/IDEA_PORTFOLIO.md` —
  active durable research state.

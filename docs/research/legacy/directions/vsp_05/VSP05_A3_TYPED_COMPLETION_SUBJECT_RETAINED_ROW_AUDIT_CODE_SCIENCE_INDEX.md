# VSP05-A3 typed completion-subject retained-row audit — code/science index

This package implements the frozen, explicitly post-A2 descriptive audit
`VSP05-A3-TYPED-COMPLETION-SUBJECT-RETAINED-ROW-AUDIT`. It performs one
offline pass over exactly the 15,971 real frontier rows in the accepted A1 raw
artifact. It does not acquire a trace, reconstruct a missing observable, use
the 47,913 static hypothetical-incumbent rows as reachable evidence, train or
evaluate a learner, or reactivate the learner route.

The immutable input is
`logs/vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json`, SHA-256
`d4ba7e00ae65c4f0cfd6f84b37c300e9e580868c42bd3c3f02eff20b0b3a3f2e`,
from source commit `1a09bccf9bd64c756865531bc55a871afa286dd3`
and accepted result commit `9f3c57f809a0c0ee11868e025adbeea762832a46`.

## Frozen labels and expected descriptive receipt

For every retained real row, the implementation takes the actual persisted
incumbent as `i` and the unchanged logged proposal as `q`. Eligibility is
`F and I and q != i`. Target labels use `G_i,T_i`; sham labels use `G_q,T_q`.
Both are recomputed from the row's complete all-skill classification. Neither
label reads reward, duration, future state/action/outcome, handoff feasibility,
or static compatibility rows.

The accepted input must independently recompute 13,379 eligible rows, 12,939
target positives, 217 target typed aliases, zero sham positives, and 141 sham
typed aliases. The 141 proposal-subject aliases remain sham facts and are not
relabeled as incumbent-subject aliases. Finite categorical group and mixed-group
counts are computed only after the epoch latches and first pending proposals
have been derived. Their serialized receipt is checked against the emitted
reduction; no row-local or stale pre-derivation 8/4 expectation is used.

## Claim-to-code map

| Protected assertion | Implementation symbols | Observable invariant | Focused evidence |
|---|---|---|---|
| Exact source bytes, path, identity, row count, and temporal order are mandatory | `load_bound_input`, `validate_retained_population`, `_validate_row` | Input path/SHA/source commit bind; 15,971 unique real IDs are processed in retained order; lifecycle ranks are complete | `test_source_loader_binds_bytes_before_json_and_rejects_hash_drift`, `test_temporal_order_and_event_rank_fail_closed` |
| Static hypothetical rows never become reachable evidence | `audit_retained_rows` source binding and `_zero_bearing_tables` | Reachable static-row use is exactly zero even if the input container holds favorable static rows | `test_same_subject_labels_recompute_i_and_q_without_relabelling_q_alias` |
| Target and sham labels preserve their subjects | `_classification`, `_row_labels`, `_descriptive_counts` | Strict truth implies the same-subject gate; q-only aliases do not increment the i-alias count | `test_same_subject_labels_recompute_i_and_q_without_relabelling_q_alias`, `test_strict_truth_without_same_subject_gate_is_rejected` |
| Eligibility is current-time and outcome-free | `_row_labels` | Only F, incumbent presence, and `q != i` enter E; future/reward fields cannot change labels | `test_future_and_outcome_fields_do_not_change_labels` |
| Derived latch/pending state is bookkeeping, not observation | `_derive_epoch_bookkeeping` | Latches are monotone/idempotent within a contiguous lifecycle/incumbent epoch and retain the first pending q even when the current q changes; the result marks them derived | `test_nulls_retain_first_pending_q_when_q_changes_within_incumbent_epoch`, `test_missing_retained_behavior_objects_fail_closed_before_passive_branch` |
| Both frozen gate/proposal nulls remain distinct and mutually consistent | `_canonical_gate_controller_null`, `_finite_categorical_reduction`, `_validate_null_receipts` | Exact controller text is protected; categorical groups project to the same canonical fields and target counts; emitted nulls equal a fresh in-memory recomputation | mixed-witness, changing-q, and controller/pending-q mutation tests |
| Every required zero stratum survives and reconciles | `_zero_bearing_tables`, `_marginal`, `_validate_zero_bearing_tables` | Cell, seed, cell/seed, lifecycle category, actual i, proposal q, and joint target/sham domains include zero counts; cell and seed marginals exactly project from cell/seed; `ineligible_join` equals the all-ineligible JOIN stratum | focused same-subject test plus empty-table, JOIN-count, and moved-cell mutation tests |
| Missing real behavior cannot be inferred from a proposal or derived latch | `_behavioral_addressability` | Pending q, observed latch, actual commit-to-q, post-commit incumbent q, first supplied-executor q input/primitive command, and necessary latch-input witness are explicit objects | `test_missing_retained_behavior_objects_fail_closed_before_passive_branch` |
| Protected result receipts are independently revalidated | `validate_audit_result` | Exact accepted source path/SHA/15,971-row binding, truth/gate and derived/observed flags, zero-bearing domains/totals, null receipts, exact missing objects, and terminal precedence cannot be changed independently | source-binding, protected-flag, zero-table/null-count, and contract-failure precedence mutation tests |
| Invalidity wins terminal precedence | `_choose_terminal_branch`, `validate_audit_result` | Any binding/integrity/activity/observable failure recomputes to `A3_INVALID_CONTRACT`, never `A3_BEHAVIORALLY_PASSIVE` | missing-object, hidden-activity, and contract-failure precedence tests |
| The audit is one-shot and zero-runtime | `run_registered_audit`, `write_result_once`, `audit_activity` | One offline audit; no environment/proposal/executor/learner/trainer/optimizer/evaluation calls, transitions, recovery, retry, or overwrite | `test_result_validator_rejects_hidden_activity_and_writer_is_one_shot`, `test_unavailable_registered_input_returns_invalid_contract_without_recovery` |

## Real-addressability fail-closed boundary

The accepted A1 retained-row schema has no observed pending-q field, observed
completion latch, actual commit-to-q/post-state incumbent, first subsequent
supplied-executor q input with its primitive command, or handoff-contract
witness that the latch is a necessary upstream commit input. The implementation
therefore preserves an exact `missing_object_witnesses` map and applies
`A3_INVALID_CONTRACT` first. It does not infer a commit by comparing later
incumbents, call a derived latch observed, fabricate a primitive command, or
downgrade missing contract objects to behavioral passivity.

## Artifact lifecycle and entry point

The thin entry point is
`scripts/run_vsp05_a3_typed_completion_subject_retained_row_audit.py` and has
one mode:

```text
python scripts/run_vsp05_a3_typed_completion_subject_retained_row_audit.py \
  --input logs/vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json \
  --output <new-a3-result.json>
```

The source is read once, hashed before parsing, and never reopened. The result
is canonical sorted JSON, written through a same-directory temporary file and
atomically installed only when the destination does not already exist. Source
binding failure still yields a typed `A3_INVALID_CONTRACT` artifact; there is
no retry, rescue, input substitution, trace recovery, or overwrite.

This implementation index records code semantics only. It is not a published
A3 result or technical acceptance record. Even the strongest scientific branch
could only make a separately named B design question askable; this package does
not select or implement B, C, External Pro, promotion, or retirement.

## Registered publication receipt (source commit 021d9bdfe733fc17cdfb9289a1b33e32008917fe)

The sole registered invocation terminated at `A3_INVALID_CONTRACT`: the runner
rejected the absolute accepted input path at registered-path binding. Therefore
`real_rows_read=0`, `registered_offline_audits=1`, and every runtime, retry,
recovery, rescue, expansion, transition, proposal, executor, learner, trainer,
optimizer, evaluation, and new-trace count is zero. The operator receipt is
`ERROR`; there was no corrected invocation, retry, new trace, runtime, or
recovery. This is a technical-acceptance rejection of the attempted audit
artifact and carries no scientific implication.

# V-K0B exposure instrumentation and identical-contract rerun — decision ledger

Status: **complete code design for touchpoint 2 conformance** (workflow 6).
Implements the ordered next action of round
`20260801_vk0_result_disposition` under Outcome B (audit:
`docs/research/cdc/EVIDENCE_NOTES/20260801_VK0B_EXPOSURE_RECOVERY_AUDIT.md`
— fields 5–8 were never accumulated and are unrecoverable). Zero
experiments run at design time; nothing here moves a threshold, estimand,
floor, seed, budget, bank, bootstrap or result mapping.

## W6-D1 — training-side exposure accumulators (counters only, no behavior change)

New accumulators on the standalone training path, incremented where the
events occur and consuming no RNG, altering no control flow:

```text
high_check_events        += number of due high checks processed per
                            maybe_assign_skills call (per env, summed)
agent_tokens_keep        += KEEP tokens emitted at those checks
agent_tokens_set         += SET tokens emitted at those checks
high_batches_attempted   += 1 per high PPO minibatch/epoch pass entered
high_batches_skipped     += 1 per pass exited without an optimizer step
                            (guard/empty/invalid branch)
aborted_batches          += 1 per batch abandoned on exception/abort path
```

At checkpoint-save time the trainer additionally reads the ACTUAL optimizer
step counters out of every optimizer state dict present
(`high_opt.state[*].step`, uniform value asserted) and records low-optimizer
absence explicitly. All of it is written durably into
`run_manifest.json` under a new `actual_exposure` block (source-labelled:
`accumulator` vs `optimizer_state`), alongside the existing
`total_steps`/`update_idx`.

**Structural disclosure (flagged for the conformance check):** there is one
shared high optimizer; distinct "high actor" vs "high value" step counters
do not exist in this architecture. The design records the shared
`high_opt` step counter and labels it `high_optimizer_steps_shared`. If
the ruling requires two distinct counters, the architecture cannot supply
them without a training-behavior change, which Outcome B forbids.

**Realization of "high-check sequences" (flagged):** realized as the count
of high-check decision events processed during training (per the
accumulator above), plus per-update values in the metrics CSV. If
"sequences" means something else (e.g. distinct per-agent sequences), say
so.

## W6-D2 — launcher and manifest fail-closed

`run_vk0b_training.py` requires the complete `actual_exposure` block after
training: any mandatory field missing, `not_available`, or derivable only
from nominal configuration → the launcher manifest records
`exposure_audit=FAILED` and exits nonzero. The old `not_available` list is
retired.

## W6-D3 — analyzer precedence-1 predicate

`analyze_vk0_result.py` gains the missing frozen row-1 condition: the
manifest must carry, per seed, all mandatory actual-exposure fields with
their source labels; a missing, inferred, or inconsistent field (e.g.
`high_opt` steps ≠ updates × configured epochs when no skip was recorded;
non-uniform per-parameter step counters) feeds
`INVALID_VARIABLE_K_URGENCY_AUDIT`. Recorded-zero low-optimizer exposure
must come from the checkpoint's optimizer-absence fact, not from config.

## W6-D4 — trace corrections (before any successor use of traces)

`audit_vk0b_r30_access.py` check rows gain the ruled `current_targets` and
`previous_targets` vectors (from the env's `_targets` arithmetic at this
and the previous check). `segment_ending_authority` is renamed in
semantics to record the authority that ENDED a segment at this row
(`voluntary_set` on the row where a SET ended the incumbency;
`episode_termination` on the final check row of an episode; the other
ruled authorities structurally unreachable in this config are still
enumerated); rows where no segment ended carry `none_open`. Schema bump:
`trace_schema_version = "vk0-trace-2"`.

## W6-D5 — identical-contract rerun

Same six seeds 2026080101–2026080106, same config module untouched, same
640,000-step / 1,000-update budget, same optimizer settings, same frozen
evaluation seed bank and 32/32 order split, same floors, same bootstrap,
same first-match mapping. Fresh output roots `logs/vk0b_r2/<seed>`; fresh
evaluation root `logs/vk0b_r2_eval`. The historical `logs/vk0b/*`
checkpoints remain diagnostic references; no pooling in either direction.
The V-K0A panel and its authorization tuple are unchanged (the oracle is
untouched by this workflow).

## Frozen amendments from the conformance ruling (round 20260801_vk0b_rerun_exposure_conformance, CHANGES_REQUIRED)

**A-W6-1 (shared-optimizer parameter-coverage proof).** Frozen:
`high_optimizer_semantics = SHARED_ACTOR_VALUE_OPTIMIZER`;
`high_actor_optimizer_steps = high_value_optimizer_steps =
high_optimizer_steps_shared` — valid only with the coverage certificate:
every trainable parameter of the R30 high actor AND of the high value
module is present in `high_opt.param_groups`, every such parameter has an
optimizer-state step entry, all those steps are equal, and the shared
count is exactly 3,000. The manifest durably carries:
`high_optimizer_steps_shared`, `high_actor_parameter_count_expected`,
`high_actor_parameter_count_with_step_state`,
`high_value_parameter_count_expected`,
`high_value_parameter_count_with_step_state`, `high_optimizer_step_min`,
`high_optimizer_step_max`, `high_optimizer_parameter_coverage_ok`.
Uniformity over whatever entries happen to exist is NOT a certificate.

**A-W6-2 (exhaustive high-pass partition; exact-exposure gate).** Expected
high optimizer opportunities are counted BEFORE any early-return guard;
every opportunity receives exactly one terminal status —
`STEPPED | SKIPPED_NORMAL(reason) | ABORTED(reason)` — with
`N_attempted = N_stepped + N_skipped + N_aborted`. For the identical
contract the identities are: completed outer updates = 1,000; high epoch
passes attempted = stepped = 3,000; skipped = aborted = 0;
`high_optimizer_steps_shared` = 3,000. The analyzer gate is amended from
"consistent unless a skip was recorded" to: **any nonzero skipped or
aborted high pass — however honestly recorded — is
`INVALID_VARIABLE_K_URGENCY_AUDIT`, reason
`TRAINING_OPTIMIZER_EXPOSURE_MISMATCH`**; likewise interactions ≠ 640,000,
outer updates ≠ 1,000, nonzero low-level exposure, incomplete
actor/value coverage, or a sequence/token-count mismatch.

**A-W6-3 (completed-sequence definition).**
`high_check_sequences_completed` counts successful R30 edit-sequence
emissions where `act_sequence` completed, the complete token vector was
produced, and the decision row was committed to the high buffer.
Initial-assignment sequences COUNT. A due call that exits before
committing appears only under an explicit failure/skipped counter, never
in the completed count. Structural identity enforced:
`N_KEEP + N_SET = 2 × high_check_sequences_completed`. No per-agent
sequence object exists.

**A-W6-4 (non-lossy segment-ending representation).** Two explicit fields
replace the single scalar:
`incumbent_end_authority_at_check ∈ {voluntary_set, none_open}` and
`post_window_end_authority ∈ {episode_termination, active_mask_change,
team_intent_boundary, forced_renewal, none_open}` (the middle three
structurally unreachable here but legal schema values). A final-check SET
carries both non-`none_open` values; `initial_assignment` is a
segment-origin value and never enters the ending vocabulary. The analyzer
may ignore both fields for current statistics; `vk0-trace-2` validates
them.

**A-W6-5 (immutable propagation of the exposure block).**
`actual_exposure_schema = "vk0b-exposure-1"`. Chain: training
`run_manifest.json` carries the source-labelled `actual_exposure` block
(allowed labels frozen: `runtime_counter`, `training_accumulator`,
`optimizer_state`, `checkpoint_optimizer_absence`; `config`/`nominal`/
`expected`/`derived_from_budget` inadmissible) → the launcher manifest
records the run-manifest SHA-256, checkpoint SHA-256 and
`exposure_audit = PASSED|FAILED` → `audit_vk0b_r30_access.py` copies the
exact block and its source-manifest hash into the per-seed evaluation
manifest → `analyze_vk0_result.py` independently validates the complete
block before row 2.

**A-W6-6 (Gate-B noninterference witness).** One proof-sized
non-scientific witness: with identical initial state and seed, enabling
the counters preserves token, action, reward, optimizer and parameter
trajectories byte-for-byte apart from the new counter/manifest fields.
Implementation conformance, not an experiment.

## W6-D6 — what is deliberately NOT done

No V-K0C work (gated on the rerun's analysis); no training-architecture or
order-randomization change; no new seeds, interactions, checkpoints or
tuning; no threshold or predicate change beyond adding the ruled missing
row-1 condition; the two trace fixes do not alter any registered statistic
of the recorded historical run.

## Cost (informational)

Instrumentation is counters + manifest plumbing (small). Rerun: six
trainings ≈ 40 min each in two-concurrent waves ≈ 2 h; evaluation ≈ 30 min;
analysis ≈ 1 min. All local; `check_compute_free.ps1` gates timing.

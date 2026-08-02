# V-K0B exposure instrumentation and rerun design conformance check

Touchpoint 2 of workflow 6. One question: **does the completed code design
in `docs/research/designs/VK0B_RERUN_EXPOSURE_DECISION_LEDGER.md` conform
to the disposition you issued in round `20260801_vk0_result_disposition`?**
Zero experiments have run in this workflow. Discarding this question's
structure is a legitimate answer.

## Variable-k relevance

This design restores the auditability your disposition requires so the
V-K0B carrier question — whether unrestricted R30 naturally accesses the
identified renewal urgency — can be answered validly.

## Frozen inputs (not review surface)

- Your disposition: V-K0A stands; V-K0B invalid
  (`REQUIRED_TRAINING_EXPOSURE_NOT_AUDITABLE`); ordered next action;
  identical-contract rerun permitted because the result is invalid, not
  adverse-valid.
- The completed exposure recovery audit
  (`docs/research/cdc/EVIDENCE_NOTES/20260801_VK0B_EXPOSURE_RECOVERY_AUDIT.md`):
  fields 1–4, 9, 10 recovered and internally consistent at every seed
  (640,000 / 1,000 / `high_opt` step = 3000 uniform / low optimizers
  absent); fields 5–8 never accumulated anywhere — **Outcome B**.
- The V-K0 realization ledger and its conformance closure; the V-K0A panel
  and authorization tuple are untouched by this workflow.

## The design, in one paragraph (full detail in the ledger)

W6-D1 adds training-side accumulators (high-check events, KEEP/SET token
counts, attempted/skipped high batches, aborted batches — counters only,
no RNG, no control-flow change) plus checkpoint-save-time extraction of
the actual optimizer step counters, all written durably into
`run_manifest.json` under a source-labelled `actual_exposure` block.
W6-D2 makes the launcher fail closed on any missing or nominal-derived
field (the `not_available` list is retired). W6-D3 adds the missing
frozen row-1 predicate to the analyzer: per-seed mandatory exposure
fields with source labels, consistency checks (`high_opt` steps vs
updates × epochs with no recorded skip; uniform per-parameter counters),
inferred-zero rejection. W6-D4 fixes the two trace fields
(`current_targets`/`previous_targets`; `segment_ending_authority` becomes
the ending authority, `none_open` when no segment ended;
`trace_schema_version` bumps to vk0-trace-2). W6-D5 reruns the identical
contract — same six seeds, config, budget, optimizer settings, evaluation
bank, order split, floors, bootstrap, result mapping — into fresh roots,
with the historical checkpoints kept as diagnostic references and no
pooling. W6-D6 does nothing else: no V-K0C work, no architecture change,
no order randomization, no new seeds or tuning.

## Points where the design interprets the disposition (flagged)

1. **Shared high optimizer.** There is one `high_opt`; distinct
   "high actor" vs "high value" optimizer-step counters do not exist
   structurally. The design records the shared counter as
   `high_optimizer_steps_shared` and labels the fact. Supplying two
   distinct counters would require a training-behavior change, which
   Outcome B forbids. Say whether the shared counter satisfies the two
   ruled fields.
2. **"High-check sequences"** is realized as the count of high-check
   decision events processed during training (accumulator; per-update
   values in the metrics CSV). If "sequences" means a different object,
   say so.
3. **Counters count, never gate**: the new accumulators change no training
   behavior; a skipped/aborted batch is recorded, not repaired. The
   fail-closed checks live only in the launcher manifest and the analyzer.

## Required response sections

1. `CONFORMANCE` — CONFORMS, or the exact ledger items that deviate.
2. `INTERPRETATIONS` — accept/correct the three flagged readings.
3. `CONVERGENCE_DECISION` — your closing decision for this touchpoint.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/VK0B_RERUN_EXPOSURE_DECISION_LEDGER.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260801_VK0B_EXPOSURE_RECOVERY_AUDIT.md`
- `docs/external-review/rounds/20260801_vk0_result_disposition/21_PRO_OPEN_RAW.md`
- `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md`
- `scripts/run_vk0b_training.py`
- `scripts/audit_vk0b_r30_access.py`
- `scripts/analyze_vk0_result.py`
- `ha_ctse_process/train.py`

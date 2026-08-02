# V-K0B valid identical-contract rerun result

Touchpoint 3 of workflow 6: the result submission. One decision is
requested. Discarding this question's structure is a legitimate answer.

## Variable-k relevance

This round submits the now-auditable V-K0B carrier result — whether
unrestricted R30 naturally accesses the identified renewal urgency — and
asks for its disposition and the next variable-k step.

## Frozen inputs (not review surface)

- Your prior disposition (V-K0A stands; historical V-K0B invalid;
  identical-contract rerun ordered under Outcome B) and the workflow-6
  conformance closure (rounds `20260801_vk0_result_disposition`,
  `20260801_vk0b_rerun_exposure_conformance`; frozen contract
  `docs/research/designs/VK0B_RERUN_EXPOSURE_DECISION_LEDGER.md` with
  amendments A-W6-1..6).
- The V-K0A panel and authorization tuple, unchanged.

## What was run (mechanical facts, PM-verified)

1. **Instrumentation implemented as frozen** (all eight of your named
   negative witnesses watched red then green; the counters-not-gates
   noninterference witness passed via a real toggle: byte-identical
   tokens, RNG and optimizer/parameter state with instrumentation on vs
   off).
2. **Identical-contract rerun**, six seeds 2026080101–2026080106 into
   fresh roots `logs/vk0b_r2/<seed>`: exposure audit **PASSED 6/6** with
   the exact frozen identities per seed — 640,000 environment
   interactions; 1,000 completed outer updates; high epoch passes
   attempted = stepped = 3,000, skipped = aborted = 0;
   `high_optimizer_steps_shared` = 3,000 with the actor/value
   parameter-coverage certificate true; token identity
   `keep + set = 2 × 128,000` completed sequences (e.g. seed 101:
   6,239 KEEP + 249,761 SET); low-level optimizer exposure 0 from
   checkpoint optimizer absence.
3. **Empirical noninterference at full scale**: every rerun final
   checkpoint SHA-256 is byte-identical to its historical counterpart
   (6/6) — the instrumented training reproduced the original training
   exactly, so the historical diagnostic observation carries over to
   provably the same policies.
4. **Evaluation** (driver with vk0-trace-2 rows: target vectors, the
   two-field segment-ending representation, exposure-block propagation
   with source-manifest hash verification): zero replay mismatches;
   5,376 check rows and 107,520 counterfactual unit rows
   (`logs/vk0b_r2_eval/`, SHA-256 `72165061…`, `51fe3e15…`).
5. **Analyzer** (with the frozen row-1 exact-exposure predicate active —
   it verifiably fires: an interim analyzer-side schema-shape defect on
   the two reasons-list fields produced a full row-1 refusal across all
   six seeds before the analyzer was corrected to the frozen producer
   shape and the analysis rerun; the row files were never touched):

```text
RESULT = row 4, R30_TOY_ACCESS_NOT_ESTABLISHED   (VALID this time)
  row 1 not triggered (complete exposure chain verified)
  row 2 not triggered (panel verdict IDENTIFIED)
  row 3 not triggered (support floor met for every seed)
  row 4 competence floor TRIGGERED

canonical order   slow_match LCB95 = 0.9961   fast_match LCB95 = 0.9931
reversed order    slow_match LCB95 = 0.4401   fast_match LCB95 = 0.5955
floor             0.75 under BOTH orders  ->  FAIL
```

The numbers equal the historical run's exactly — necessarily, since the
checkpoints are byte-identical and the evaluation contract is frozen.

## Decision requested

**The disposition of the now-valid V-K0B row-4 result, and the next
scientific step.** Your prior disposition pre-ordered: "If a valid V-K0B
analysis again produces row 4, the next conclusion-bearing scientific
experiment should be V-K0C — R30 autoregressive order-transport
localization" (no training; exact joint-edit-distribution enumeration
under both orders at matched states; deterministic prescribed-assignment
positive control; fresh-vs-trained comparison; your five-outcome
classification table). Open questions, unranked:

1. Is the row-4 result now a valid adverse finding for the competence
   floor under reversed serialization, and what unit does it retire or
   support?
2. Does V-K0C proceed exactly as pre-specified, or does the valid row-4
   change its design (states, controls, classification table)?
3. The V-K0C checkpoints: the rerun checkpoints are byte-identical to the
   historical ones — which set is the named reference for V-K0C's
   "valid frozen checkpoints"?

## Required response sections

1. `DISPOSITION` — smallest unit retired/supported; portfolio delta.
2. `VK0C_DESIGN` — confirm or amend the pre-specified V-K0C, including
   its evidence design and result semantics.
3. `CORRECTIONS` — any fact above that is wrong.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/VK0B_RERUN_EXPOSURE_DECISION_LEDGER.md`
- `docs/external-review/rounds/20260801_vk0_result_disposition/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260801_vk0b_rerun_exposure_conformance/22_PRO_CONVERGENCE.md`
- `docs/external-review/rounds/20260801_vk0b_valid_rerun_result/60_EVIDENCE/summary.json`
- `docs/external-review/rounds/20260801_vk0b_valid_rerun_result/60_EVIDENCE/train_and_checkpoint_manifest.json`
- `scripts/audit_vk0b_r30_access.py`
- `scripts/analyze_vk0_result.py`
- `ha_ctse_process/train.py`

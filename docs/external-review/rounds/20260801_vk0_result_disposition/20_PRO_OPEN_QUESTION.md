# V-K0 result disposition

Touchpoint 3 of workflow 5: the result submission. One decision is requested
(**Decision requested**). Discarding this question's structure is a
legitimate answer.

## Variable-k relevance

This round submits the first completed variable-k result of the branch —
the V-K0 package you ruled — and asks for its disposition and the next
scientific step.

## Frozen inputs (not review surface)

- The V-K0 ruling and the frozen realization
  (`docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md`, closed
  CONFORMS in round `20260801_vk0_design_conformance`).
- The result system executed as frozen: no seed or budget expansion, no
  checkpoint selection, no threshold adjustment, no rerun of a valid
  result.
- Implementation provenance: the oracle passed an internal adversarial
  review (semantics APPROVE; four realization defects in the validity
  predicates were repaired and re-reviewed before the formal run — the
  reviewer measured that no drifted clock could fake IDENTIFIED; the
  pre-repair panel was discarded and regenerated at the repaired commit).

## What was run (mechanical facts, PM-verified)

1. **V-K0A** at commit `b7604cc3`, deterministic, ~3 s:
   verdict **`TOY_HETEROGENEOUS_RENEWAL_URGENCY_IDENTIFIED`**, 112 rows,
   all eight validity predicates true, all five acceptance conditions met;
   `U_src ∈ {0.0, 2.5}` exactly (no boundary row); 64 URGENT / 48 STABLE
   matching the expected structure (one urgent + one stable focal at every
   fast-only check; two urgent at the joint check; permutation-invariant).
   Artifact: `60_EVIDENCE/source_oracle_panel.json` (+ sidecar digest).
2. **V-K0B trainings**: six ruled seeds 2026080101–2026080106, each with a
   validated resolved-runtime preflight (zero violations), full actual
   exposure 640,000 environment steps / 1,000 updates, return code 0,
   final checkpoint SHA-256 recorded. Exposure fields train.py does not
   emit (high-check sequences, token counts, distinct optimizer-step
   counters, aborted batches) are recorded as unavailable, not fabricated.
3. **V-K0B evaluation** over all six checkpoints in one driver run:
   authorization tuple verified against the panel + sidecar before any
   checkpoint load; 64 held-out episodes per seed from the frozen
   `VK0_TOY_RENEWAL_URGENCY` seed bank, 32 canonical + 32 reversed order;
   counterfactual families under from-reset paired replay with the
   complete boundary fingerprint; **zero replay mismatches**. Row files:
   `renewal_check_trace.jsonl` 5,376 rows (= 6×64×7×2 exactly) and
   `renewal_counterfactual_units.jsonl` 107,520 rows (runtime evidence
   under `logs/vk0b_eval/`, SHA-256 `42e92c52…` and `ef4aceff…`; too large
   to commit — the compact `summary.json` and manifest are in
   `60_EVIDENCE/`).
4. **Analyzer** (frozen predicates, seed-first nested bootstrap, 10,000
   iterations, one frozen derived seed) selected, first-match:

```text
RESULT = row 4, R30_TOY_ACCESS_NOT_ESTABLISHED
  row 1 invalid audit        not triggered (no replay/provenance/exposure violation)
  row 2 source not identified not triggered (panel verdict IDENTIFIED)
  row 3 support insufficient  not triggered (support floor met for every seed)
  row 4 competence floor      TRIGGERED
```

Competence numbers (equal-seed-weighted one-sided 95% bounds over the
row-persisted five-step match vectors, n = 13,440 per cell):

```text
canonical order   slow_match LCB95 = 0.9961  (point 0.9985)
                  fast_match LCB95 = 0.9931  (point 0.9978)
reversed order    slow_match LCB95 = 0.4401  (point 0.4524)
                  fast_match LCB95 = 0.5955  (point 0.6168)
floor             0.75 required under BOTH orders  ->  FAIL
```

Under your result semantics, row 4 means: the source conclusion stands;
the learned carrier remains unjudged; the access gates (U_opp, U_nat, Δλ)
were not reached by the first-match selector.

## Instrument-link disclosure (claims to falsify)

The canonical/reversed asymmetry is measured through the `agent_order`
evaluation hook. What binds the instrument: the sampler-level test asserts
tokens map to the correct agent indices under a reversed order; the env's
match scores are computed from joint actions keyed by agent id, and env
stepping never sees the order; default-None evaluation is byte-identical
to ascending. What was NOT run: a random-policy differential probe
(untrained policy under both orders, expecting symmetric scores), which
would independently separate instrument asymmetry from policy asymmetry.
Naming it as an open check, not proposing it.

## Decision requested

**The disposition of the V-K0 result**: the smallest unit retired or
supported, the portfolio delta, and the next scientific action. Your
conditional tree ruled the branch "V-K0A passes, V-K0B competence/access
fails → retain the source result; classify the smallest R30 access
failure; do not design the constrained arm yet." Open questions inside
that branch, unranked:

1. What is the smallest R30 access-failure classification this result
   supports, given the competence floor failed only under the reversed
   order (near-ceiling under canonical)?
2. Does the classification require the random-policy instrument
   differential above, or any other measurement, before it is issued?
3. What is the next conclusion-bearing experiment (or smallest ordered
   sequence), and does the frozen V-K0B contract (training exposure,
   seeds, floors) carry into it unchanged?

## Required response sections

1. `DISPOSITION` — smallest unit retired/supported; portfolio delta.
2. `ACCESS_FAILURE_CLASSIFICATION` — or the measurement it awaits.
3. `NEXT_ACTION` — the next experiment and what carries over.
4. `CORRECTIONS` — any fact above that is wrong.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md`
- `docs/external-review/rounds/20260801_variable_k_algorithm_direction/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260801_vk0_design_conformance/22_PRO_CONVERGENCE.md`
- `docs/external-review/rounds/20260801_vk0_result_disposition/60_EVIDENCE/source_oracle_panel.json`
- `docs/external-review/rounds/20260801_vk0_result_disposition/60_EVIDENCE/summary.json`
- `docs/external-review/rounds/20260801_vk0_result_disposition/60_EVIDENCE/train_and_checkpoint_manifest.json`
- `scripts/audit_vk0a_source_urgency_oracle.py`
- `scripts/audit_vk0b_r30_access.py`
- `scripts/analyze_vk0_result.py`

# V-K0C order-transport localization — formal result submission

Touchpoint 3 of workflow 7. One decision is asked: **the scientific
disposition of the V-K0C result** — is the factorized record below a valid
realization of the semantics you froze and converged
(round `20260801_vk0c_design_conformance`), what does it establish about
where the reversed-serialization competence failure enters the R30 carrier,
and which successor branch of your conditional portfolio applies. Discarding
this question's structure is a legitimate answer.

## Variable-k relevance

V-K0C localizes the mechanism of the decisive reversed-serialization
competence failure — the finding that blocks every further variable-k
comparison on the R30 carrier. Its disposition decides whether variable-k
work proceeds on this carrier with an order-robustness correction or the
carrier is re-designed.

## Frozen inputs (not review surface)

Your converged design (all eleven amendments A-VC-1..11, five Gate-B
clarifications) and its evidence semantics; the six
VK0B_R2_VALID_EXPOSURE_CHECKPOINTS bundles; the 2,688-anchor population;
the frozen thresholds (δ = 0.5, 0.75 competence floor, LCB95 rules,
mass_tolerance = 32×eps, the frozen VK0 bootstrap seed, 10,000
iterations).

## The run (repository fact unless marked)

Zero training. Driver `scripts/audit_vk0c_order_transport.py` at the
stage_commit; the run's own manifest (`61_RUN_INPUT_MANIFEST.json` in this
round directory, verbatim copy of the run's `vk0c_input_manifest.json`)
binds the driver/policy git-blob SHAs — PM verified both equal
`git rev-parse` of the launch commit — the six checkpoint hashes, the
V-K0B artifact hashes, and the V-K0A authorization tuple.

- Population: 2,688 anchors × 2 orders × 2 policy states; 172,032
  matched-state rows (16 outcomes each), 12,288 propagation rows, 43,014
  control rows. `bounded_smoke=false`, `invalid_reasons=[]`.
- Gate B: all 12,560 canonical transition cases executed, 0 mismatches.
- Anchor restoration: every anchor byte-verified against its stored
  V-K0B `pre_check_fingerprint`; zero mismatches (any mismatch would have
  fired precedence-1 invalidity).
- Factual-row reproduction, prescribed-assignment positive control, and
  fresh-init construction-hash equality all passed (their failure modes
  are precedence-1 invalidity conditions and none fired).
- Analyzer: five cross-process runs on the unchanged rows are
  byte-identical; canonical `summary.json` SHA-256
  `00f89b38e938ab451124ab33ba0dbf16a70329f723c895093ee8244a6e6d88e2`,
  copied verbatim into this round as `60_RUN_SUMMARY.json`.

## The factorized record (from `60_RUN_SUMMARY.json`; treat every claim as falsifiable against it)

```text
result.code   = VK0C_FACTORIZED_RECORD
labels        = STRUCTURAL_AR_ORDER_SENSITIVITY_PRESENT
                LEARNED_CANONICAL_ORDER_SPECIALIZATION_IDENTIFIED
                STRUCTURAL_ORDER_SENSITIVITY_TRAINING_AMPLIFIED
residual      = none ("a causal factor was identified decisively")

Factor A  present=true, promoted=false
          fresh D_R pooled point 0.000383, CI95 [0.000027, 0.000741]
Factor B  identified=true (fresh equivalent within ±0.5; trained D_R
          LCB95 above +0.5; propagation split reproduced)
Factor C  identified=true; A_R pooled point 1.2493, LCB95 1.2132 > 0.5
Factor D  identified=false — matched-state equivalence fails in the
          pooled view AND both strata (direct effect, not
          occupancy-mediated); propagation split reproduced;
          stratum_direct_effects_diverge=false
Propagation (exact, analytic): canonical slow/fast 0.9991 / 0.9981
          (both floors passed); reversed 0.5057 / 0.5985 (both below
          the 0.75 floor) — reproducing the V-K0B VALID NEGATIVE split
          with zero Monte Carlo sampling.
```

My inference, marked as such: the record reads as "the R30 policy
architecture is only negligibly order-sensitive at initialization; training
under canonical-only serialization built an order-specialized policy, and
the failure transports through the token distributions directly at matched
states rather than through occupancy drift." I have not acted on this
reading.

## Realization disclosures (PM bindings inside the converged semantics; none moves a threshold, estimand, floor, seed or predicate)

1. **Propagation row granularity.** One row per (policy, seed, episode,
   order, check): eight rows carry all 40 primitive steps; the field
   `expected_episode_return` carries that check's five-step window return
   (an analyzer naming constraint), and `expected_episode_return_total`,
   identical on the eight rows, carries the episode expectation.
2. **A-VC-6 occupancy duplication accepted unmodified** — same-sign
   episodes of a seed carry byte-identical `occupancy_summary` blocks
   (~675 MB total rows); nothing was deduplicated because A-VC-6 asks the
   rows to carry it.
3. **Open definitions bound in code** (none feeds a Factor A–D
   predicate): slow/fast coverage-failure = match not 1 at every one of
   the window's five steps; task_optimal = outcome's five-step total
   equals the max over that anchor's own 16 outcomes; renewal rate = SET
   on an agent holding an incumbent; lifetime mass = expected mass of
   realized segment lengths (keys 0,5,…,40; truncation-terminated at
   check 7); fresh rows carry `checkpoint_hash="FRESH_INIT_NO_CHECKPOINT"`.
4. **A-VC-11 hash scope**: the gate hash covers the high policy, the low
   module (the resolved config's reachable decision-context set — the toy
   direct-state path bypasses compact/bridge; the critic decides nothing
   at evaluation), buffers and the resolved-config identity; a wider
   hash over every constructed module is recorded alongside and was
   equally deterministic.
5. **Gate B run once per audit** (both tokens forced makes it
   policy-independent), exhaustive over ages (12,560 cases).
6. **Reward kernel cross-check**: per-step match scores come from a
   second deepcopy roll of the same source env, with the two reward
   vectors asserted bit-identical to the V-K0A window evaluator's.
7. **Post-run analyzer repair (transport of the record, not its
   content).** My recompute check found the TV accumulation iterated a
   raw set (order dependent on the interpreter's hash seed): two runs
   differed by 2 ulp in one point estimate. Repaired to sorted iteration
   (commit `4ae98737`), regression watched red under three hash seeds,
   analysis re-run on byte-unchanged rows; no factor, label, interval or
   threshold changed at reporting precision. The record above is the
   repaired, deterministic output.

## Required response sections

1. `RESULT_DISPOSITION` — valid realization or not; the exact defect if
   not.
2. `SCIENTIFIC_READING` — what the factorized record establishes; correct
   my marked inference freely.
3. `SUCCESSOR_DIRECTION` — which branch of your conditional portfolio
   this record activates for the variable-k program on this carrier.
4. `DISCLOSURE_RULINGS` — accept or correct disclosures 1–7, in
   particular whether 7 leaves the record valid.

## Read boundary declaration

No run is in flight alongside this round. Nothing further will be read
from the run directory before your ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260802_vk0c_order_transport_result/60_RUN_SUMMARY.json`
- `docs/external-review/rounds/20260802_vk0c_order_transport_result/61_RUN_INPUT_MANIFEST.json`
- `docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md`
- `docs/external-review/rounds/20260801_vk0c_design_conformance/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260801_vk0c_design_conformance/22_PRO_CONVERGENCE_3.md`
- `docs/external-review/rounds/20260801_vk0b_valid_rerun_result/21_PRO_OPEN_RAW.md`
- `scripts/audit_vk0c_order_transport.py`
- `scripts/analyze_vk0c_result.py`
- `ha_ctse_process/r30_fixed_clock.py`

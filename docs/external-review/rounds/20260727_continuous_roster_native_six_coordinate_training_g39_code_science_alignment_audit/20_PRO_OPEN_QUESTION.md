# External Pro open question: G39 code-science alignment

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
compute_budget=zero
audit_target_commit=6d8b18066d312d8733d08a9e9356f12760ec2f79
implementation_code_commit=6d8b18066d312d8733d08a9e9356f12760ec2f79
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_INDEX.md
frozen_contract=docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/21_PRO_OPEN_RAW.md
nonformal_compute_started=false
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_coordinate_training_g39.py`
- `scripts/run_continuous_roster_native_six_coordinate_training_g39.py`
- `tests/ha_ctse_process_continuous_roster_native_six_coordinate_training_g39_test.py`
- `tests/run_continuous_roster_native_six_coordinate_training_g39_test.py`

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
the exact pushed audit target and the allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. The index is navigation, not a substitute for
reading the named implementation.

Question: does Code Project Manager's accepted implementation instantiate the
exact frozen G39 `CONST10_FOLD6` versus `NATIVE6_CS` paired-training contract,
with function-matched initialization, equal source information and exposure,
the intended 136-scalar/Adam/fold treatment only, exact paired evaluation and
confidence plan, and the frozen first-match disposition semantics—without a
different route to either conclusion-bearing branch?

Check only these conformance points:

1. CONST has true ten-coordinate `Linear(10,32)` and `Linear(10,2)` raw maps;
   NATIVE is born with true six-coordinate maps, has no filler/constant column
   or fold path, and removes exactly 136 parameters without changing the
   downstream actor, critic, credit, lifecycle or action-distribution contract.
2. For every replicate NATIVE derives deterministically from the single CONST
   initialization: `W_N=W_C[:,0:6]`, `b_N=b_C+W_C[:,6:10]@c`, with
   `c=(1/2,1/2,1/2,24/47)`. Every unaffected actor, critic, baseline and
   log-standard-deviation tensor is bitwise copied; all model, buffer and Adam
   state ownership is separate.
3. Both arms receive, store and optimize only the same six varying source
   coordinates. CONST appends the four constants only internally; inactive rows
   remain zero. Initial folded CONST and NATIVE checkpoints, then their first
   paired 8-episode, 48-step trajectories, meet the exact raw-contract
   bitwise/`1e-7`/`1e-6` and lifecycle/source/roster predicates before updates.
4. The fast and RTG analytic gradient relations are finite and satisfy the
   frozen `1e-6` bound. Their elementwise union makes every one of the 136
   removable CONST scalars and every NATIVE effective-bias scalar live above
   `1e-12`; column-level liveness alone is not sufficient.
5. Both paired trajectories are collected before either update. Fast Adam is
   discarded at phase transition; fresh direction-balanced actor/critic Adam
   states are separate; both arms get exact equal PPO exposure; only final
   learned checkpoints persist; CONST folds only after training and receives no
   fold-time optimization.
6. The nonformal/formal inventories, seed law, CPU-only caps, `H=48`,
   `K_search=0`, zero hypothetical transitions, G34 fixed/random capacities
   `6|8|12`, five cells, rotating `22/21/21` process counts, whole-episode
   paired bootstrap, exact access/comparison equality rules and ordered five
   result branches match the frozen contract.
7. Evaluation uses exact paired ledger, event-signature and member-owned action
   mates; CONST deploys only its exact final fold and NATIVE remains truly
   six-wide. Formal execution fail-closes without the same-source `ALIGNED`
   result, exact token and the three required bounded-preflight artifacts.

A positive result supports only this exact native-six training
parameterization under G39-P0. A mismatch can identify only an exact frozen
assertion and conflicting code behavior plus the smallest in-contract
correction. This audit cannot establish task-level history necessity, native-six
inexpressivity, a new threshold, a new algorithm, extra evidence, a runtime
run, or formal authorization.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the target instantiates the frozen contract
  without an indexed test/probe admitting a result-changing wrong mechanism.
- `AUDIT_DISPOSITION=MISMATCH` only with the exact frozen assertion, conflicting
  code path or behavior, and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated,
  result-changing scientific choice that prevents conformance judgment.

Do not accept or redesign code. Stop after the single scoped disposition.

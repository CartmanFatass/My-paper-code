# Disposition — Variable-N + Variable-Lifetime Implementation Review

## Final verdict

`MODIFY_PLAN`

The architecture remains implementable without identity, fixed slots or an
F1-only module, but implementation must follow the corrected ownership,
transaction, low-policy, critic, replay and strict-resume contracts.

## Accepted corrections

- One policy-runtime `LifecycleStore` lives in the event runtime. The
  environment worker owns physical state/facts; the collector transports typed
  transactions and owns no policy lifecycle shadow.
- Temporary leave uses a post-transition/pre-removal critic snapshot, an atomic
  typed membership delta and a post-membership/pre-policy snapshot.
- Event mode owns one new trainable actor-only, active-ragged low policy plus a
  separate shared active-set critic. Legacy classes and checkpoints remain
  unchanged and are not wrapped or migrated.
- Every event token's old value uses its exact pre-token working centralized
  context in both F0 and F1.
- Schema 3 live resume includes simulator/worker state, environment RNG,
  collector presentation/pending transaction and current observation/state.
  The mode/header is read before collector reset or fixed-N construction.
- F0/F1 match the data-generation contract, external randomness contract and
  exposure budget. Treatment-induced on-policy trajectory divergence is part
  of the estimand, not a mismatch.
- F1 wiring evidence is a common-support relative-score change under a
  constructive control, not merely a nonzero prefix Jacobian.
- The focused test, production code and one canonical log remain the evidence
  sources. No duplicate tracked acceptance JSON is added.

## File boundary

The corrected production boundary is:

- new `ha_ctse_process/variable_roster_event.py`;
- early event dispatch and strict schema-3 load/save in
  `ha_ctse_process/train.py`;
- default-off typed transaction and snapshot transport in
  `ha_ctse_process/collectors.py`;
- one deterministic transaction test in
  `tests/ha_ctse_process_variable_roster_event_test.py`.

`ha_ctse_process/standalone_agent.py`, `r30_fixed_clock.py`, legacy/R30
checkpoints, environments and rewards are not modified by this plan.

## Authorization and stop

The two design documents are corrected now. A later user-approved production
implementation may proceed only through one hand-authored deterministic trace
covering lifecycle transitions, ragged replay, update truncation, exact live
resume, permutation compatibility, F0 reduction and F1 common-support positive
control.

Stop before any real environment construction/reset/step, subprocess worker,
environment-data optimizer step, benchmark, training, scientific PASS/FAIL or
claim that F1 is useful or integrated.

If correctness passes but F1 changes only masks, a common additive logit shift
or no normalized common-support distribution, retire H1 and adopt `STOP_AT_F0`.
If correctness requires identity, slots, F1-only capacity, team latent, graph,
learned order or learned event time, also stop at F0 rather than stacking
modules.

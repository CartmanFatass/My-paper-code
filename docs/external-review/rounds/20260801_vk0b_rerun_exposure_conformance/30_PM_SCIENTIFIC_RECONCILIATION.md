# Reconciliation — 20260801_vk0b_rerun_exposure_conformance

Ruling: `21_PRO_OPEN_RAW.md` (CHANGES_REQUIRED) then `22_PRO_CONVERGENCE.md`
(CONFORMS), stage commit `2b49152b11e46d05bdc9d46611002dc8f2b46626`.

## What was decided

First turn: the identical-contract rerun route is correct (Outcome B —
retrying a failed operational realization is permitted; rescuing a valid
result is not), with five blocking amendments: (1) the shared high
optimizer is admissible only with a parameter-coverage certificate (both
actor and value parameter sets fully covered, per-parameter step state
present and uniform at exactly 3,000, eight durable manifest fields);
(2) high-pass statuses form an exhaustive partition counted before any
early-return guard, and ANY nonzero skipped/aborted pass — however
honestly recorded — is `INVALID_VARIABLE_K_URGENCY_AUDIT /
TRAINING_OPTIMIZER_EXPOSURE_MISMATCH` ("recording a deviation does not
make that deviation admissible"); (3) `high_check_sequences_completed`
counts committed autoregressive edit sequences (initial assignments
included) with the identity `N_KEEP + N_SET = 2 × sequences`; (4) the
segment-ending scalar is replaced by two fields
(`incumbent_end_authority_at_check`, `post_window_end_authority`) so a
final-check SET can carry both events; (5) the source-labelled
`actual_exposure` block (`vk0b-exposure-1`; admissible sources frozen)
propagates immutably: run manifest → launcher manifest (with run-manifest
SHA) → per-seed evaluation manifest → analyzer validation before row 2.
Plus a Gate-B noninterference witness (counters byte-for-byte inert on
trajectories).

Convergence turn: the entered amendments (A-W6-1..6, commit `6579e440`)
**CONFORM**; every definition frozen; no new protected decision; no
further design round. The next permitted boundary is the proof-sized
implementation/Gate-B package with eight named negative witnesses (missing
actor/value parameter; parameter without step state; a skipped/aborted
pass; sequence/token mismatch; inadmissible source label; mismatched
source-manifest hash; final-check SET dual ending; instrumentation-on/off
trajectory equality). The ruling authorizes neither implementation nor
the rerun — those proceed under the PM's ordinary authority and the
user's active grant.

## Where I was corrected

- My "consistent unless a skip was recorded" analyzer gate would have
  admitted a documented-but-reduced exposure; exactness is the contract.
- My `high_batches_attempted` counted entered epoch passes and missed
  early returns before the loop — the partition must be counted at the
  opportunity, not the entry.
- My single `segment_ending_authority` scalar recreated the exact
  conflation the correction was ordered to remove (final-check SET +
  episode termination).
- "Uniform over the optimizer-state entries that exist" is not a coverage
  certificate — a parameter that never received a gradient has no entry
  and would be invisible.

## Next action

Implement the amended ledger via registered subagents (four disjoint
scopes: training instrumentation; launcher; driver trace/propagation;
analyzer), each with its named negative witnesses; then the Gate-B
noninterference witness; then the identical-contract rerun, evaluation,
analysis, and touchpoint 3.

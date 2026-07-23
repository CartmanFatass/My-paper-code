# Cross-lifecycle commitment handoff G2 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution and workflow hash handoffs are disabled.

```text
active_implementation=CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_INFORMATION_GATE
implementation_status=AUTHORIZED_NONFORMAL
design=docs/research/designs/CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2.md
backend=cpu
torch_threads=1
formal_run_status=not_launchable_until_trainable_contract_is_frozen
G1_mutation=forbidden
backward_compatibility=not_required
```

## Goal

Implement the smallest deterministic proof that creator-only information is
lost by fresh per-member recurrence at terminal handoff, while both team
recurrence and an event-held team commitment can carry it. This is a no-training
information gate, not formal iteration 3.

## Owned active line

- create `ha_ctse_process/cross_lifecycle_handoff_g2.py`;
- create `scripts/run_cross_lifecycle_handoff_g2.py`;
- create `tests/ha_ctse_process_cross_lifecycle_handoff_g2_test.py`;
- update only the active project/CDC contract paths required by acceptance.

No G0/G1 source, learner, checkpoint, runner, result selector or test is changed.

## Task 1 — Exhaustive source and information proof

**Status:** complete and PM accepted.

Enumerate the balanced bit, creator/successor/survivor packing, same-slot reuse,
cross-slot transfer and heterogeneous lifetime cases from the design. Expose an
exact successor-visible trace key and compute its Bayes-optimal bit accuracy.
Reject missing sign mates, identity leakage, nonzero successor initial state or
unbalanced physical mappings.

**Proof-sized tests:** exact case inventory and a deleted-sign-mate negative.

## Task 2 — Constructive controls and intervention

**Status:** complete and PM accepted.

Evaluate PER_MEMBER_REC, DUM, TEAM_REC, EHC and RANDOM_MARK without optimization.
Snapshot after creator departure and flip only the event-held mark under the same
future schedule.

**Proof-sized tests:** exact natural utilities, mark-flip action change/utility
drop, creator-state deletion, successor zero initialization and team-state
survival.

## Task 3 — Nonformal runner

**Status:** complete and PM accepted.

Write one compact JSON artifact containing the design identity, `formal=false`,
case inventory, exact metrics, invariant list and first-match result. Reject an
existing output root and do not persist per-case traces.

**Bounded exercise:** CPU one thread, one deterministic invocation, no Torch,
training, checkpoint, RNG or formal flag.

## Acceptance

Project Manager runs the focused test file and one fresh exercise, inspects the
implementation for identity leakage, hidden-state carryover, task-specific
reward, accidental randomness and excess persistence, then accepts or repairs.

`PASS_HANDOFF_INFORMATION_GATE_G2` advances only to a separate trainable
TEAM_REC/DUM/EHC evidence-contract definition. It consumes zero iterations;
three conclusion-bearing iterations remain. Formal CPU execution remains under
the standing user grant but is not launchable from this information gate.

Accepted evidence:

- focused test: 4 passed;
- artifact: `logs/nonformal_cross_lifecycle_handoff_g2_20260723_pm2/result.json`;
- 96 exhaustive cases, exact sign mates and 12 physical mappings;
- PER_MEMBER_REC/DUM/RANDOM_MARK `0.5`, TEAM_REC/EHC `1.0`;
- held-mark flip action change and utility drop `1.0`;
- `formal=false`, no training, optimizer, checkpoint or RNG.

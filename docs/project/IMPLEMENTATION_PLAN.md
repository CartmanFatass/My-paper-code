# Open-roster zero-shot scale G6 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hash handoffs
> are disabled.

```text
active_implementation=OPEN_ROSTER_ZERO_SHOT_SCALE_G6
implementation_status=FORMAL_COMPLETE_CLOSED_SUCCESS
design=docs/research/designs/OPEN_ROSTER_ZERO_SHOT_SCALE_G6.md
backend=cpu
torch_threads=1
training_operation=none_frozen_g5_checkpoint_import
asynchronous_skill_lifetime=frozen
formal_iteration=7
chain_iterations_remaining_after_run=10
```

## Goal

Measure the zero-shot boundary of the successful G5 checkpoint before changing
the algorithm. Separate far-count transport, unseen membership-event-time
transport and their joint composition. Preserve all G5 scientific and result
semantics.

## Task 1 - Add an evaluation-only stress ledger

Create a new ledger/environment adapter with profile-owned membership times and
capacities through 20, while active count remains at most 16. Reuse the exact
G5 count feature, horizon, wave windows, observations, actions, lifecycle and
utility. Expected demand follows actual wave arrival membership.

Focused proof: every profile validates, exact roster traces occur, constructive
utility is one, configured lifecycle transitions preserve hidden-state
ownership, and extra inactive padding cannot change active outputs.

## Task 2 - Add zero-training checkpoint intake

The runner's ordered `train` phase creates a fresh G6 root, validates the exact
closed G5 manifests/checkpoints and materializes only the three final models.
It records zero optimizer steps and never calls an update. Any source, branch,
runtime, count, checkpoint or authorization mismatch fails closed.

Focused proof: exact intake succeeds; one-field provenance tampering fails;
strict load succeeds at update 250; model state is finite and unchanged.

## Task 3 - Evaluate and analyze

Evaluate 18 cells covering three replicates, three domains and deterministic/
stochastic action selection. Serialize full episode arrays and profile names.
The analyzer validates inventory, source controls, runtime, model immutability
and the registered first-match gates.

Focused proof: a reduced nonformal full path closes operationally, formal
analysis rejects nonformal artifacts, exact 0.90 boundaries pass and the next
representable value below fails.

## Acceptance and launch

Run only the new focused test file plus one bounded nonformal exercise using the
registered CPU interpreter and one thread. After Project Manager accepts the
package and integrates it in Git, assign one exact foreground
`train(import) -> evaluate -> analyze` pipeline to the fixed Luna-low experiment
operator. A valid result consumes iteration 7 and leaves ten rounds.

Acceptance is complete: the G6-specific suite passes `7/7`, the combined G6/G5
focused suite passes `12/12`, and the post-repair nonformal path at
`logs/nonformal_open_roster_zero_shot_g6_20260723_pm2` is operationally valid
with zero optimizer steps and exact model immutability. One advisory review
found a missing G5 authorization-token provenance check; the repaired intake,
record, analyzer and two tamper cases were accepted by the same reviewer. The
package is formal-ready after Git integration.

## Formal disposition

Formal iteration 7 is operationally valid and returns
`ROBUST_ZERO_SHOT_OPEN_ROSTER_G6`. Count-scale, event-time and joint
deterministic CI95 lower bounds are respectively `0.9294811`, `0.9854642` and
`0.9358802`; the minimum joint replicate is `0.9358802` and joint stochastic
mean is `0.9501188`. All gates pass with zero optimizer exposure and exact model
immutability.

G6 is closed. The next active boundary is a zero-compute derivation for frozen-
checkpoint transport beyond the declared N=16 count-feature limit. Ten
conclusion-bearing iterations remain.

# L0 — B01 legal-input long-window schedule selector

**Status (2026-09-27 owner re-review): WITHDRAWN; do not implement or execute.** The helper
was interrupted before any candidate source, test, run or scratch directory was created.
The original task below is retained for provenance. The [final disposition](NOTES.md#2026-09-27--owner-requested-re-review-end-the-binary-selector-investment)
ends this investment; the task body below is no longer an implementation instruction.

Implement the prospective contract in the 2026-09-27 entry of this direction's
[`NOTES.md`](NOTES.md) and its [`CLAIM_long_window_schedule_value.md`](CLAIM_long_window_schedule_value.md).
That entry is the design authority; implementation must not broaden it.

## Owned scope

Create the B01 implementation and runner only under
`experiments/candidates/uav_cooperative_planning/b01/`. Use direction-owned output under
`runs/uav_cooperative_planning/<tag>/` and scratch under
`temp/directions/uav_cooperative_planning/`. Reuse existing S7-S2 H_local, feedback, environment
and metric interfaces by import where possible. Do not edit shared environment/learner code,
other candidate directions, shared tests, `scripts/`, or the RESEARCH routing block.

Implement:

1. H_local@10 and its anticipatory-rematching overlay exactly as registered: legal 30-second
return-margin secant; nominee is an unambiguous H_local service-target assignee; lead window
60 seconds; at most one nomination; zero-action wait and ordinary matcher reallocation; end on
actual shield entry or 60-second timeout; suppress a timed-out UAV until its forecast exits the
lead window or becomes nondeclining. Actual shield modes and native guard are immutable. Preserve
H_local state. Log candidate, trigger, actual entry, timeout, suppression and schedule changes.
2. Collection on 970001–970064: ten 300-step blocks/world, five blocks per schedule in a
deterministically shuffled order from `SeedSequence([970902, world_seed])`; retain only the
selected option's legal boundary context and actual next-10/next-300 native team reward sums.
3. Two offline CPU MLP regressors with the registered architecture, normalization, seed, minibatch
order, 50 passes and 500-update cap; no tuning, validation selection, extra initialization or
counterfactual labels.
4. One-use paired evaluation on 971001–971032 under the four registered arms; score selectors
every 300 steps and hold their chosen schedule for that full block.
5. Compact reproducible config/summary/status, model hashes, per-world native outcomes and
boundary decision records. Preserve technical and incomplete-window failures; never substitute
zero or automatically replace seeds.

Every selector feature must derive from the eight legal 365-field observations, documented
controller memory and the candidate schedule one-hot. Exclude raw `state`, hidden user motion or
identity, simulator objects, `plan_inputs`, synthetic/teacher labels and counterfactual returns.
Record feature-field definitions in the config.

## Handoff and checks

Return a concise diff summary, exact files, syntax/static checks and unresolved risks. Do not add
or run tests. Do not run an environment episode, fit, launcher, resource admission or scientific
batch. Stop after implementation; DM review and a separately authorized operator handoff follow.

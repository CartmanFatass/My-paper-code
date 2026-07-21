# External Review Request: EVENT_HELD_COMMITMENT_LINK_G0 Implementation

You are reviewing a completed implementation against its frozen executable
plan. Work from private repository `CartmanFatass/My-paper-code`, branch
`aggressive`, target implementation commit
`ce0d0ec2ee1dc9e2ceee15ee0b76f19ebd84573c`.

The complete change under review:

```text
git diff 5a34c16065c6b92d77f897abaa692ab88d2f2c0f ce0d0ec2ee1dc9e2ceee15ee0b76f19ebd84573c
```

## Status You Must Preserve

- The scientific route is **adopted and closed**. `EVENT_HELD_COMMITMENT_LINK_G0`
  is the authority; do not propose a successor source or reopen the objective.
- Every registered constant is frozen: seeds, thresholds (`0.78`, `0.10`,
  `0.20`, `0.25`), budget (16 envs, horizon 80, 250 updates, 5 replicates,
  320,000 transitions/arm), model sizes, evaluation cells and bootstrap design.
  Do not retune, rescale or "improve" any of them.
- The superseded noncalendar H/C/S/D benchmark, hindsight solvers,
  calendar-masked arm, old result tree and old checkpoint schema are **deleted
  on purpose**. Active-line development is the project rule; their absence is
  not an omission and compatibility shims are forbidden.
- No formal training or registered evaluation has run. Only the bounded
  non-formal smoke has executed.
- This is not a request for a general code-quality review. Style, naming,
  typing and refactoring suggestions are out of scope unless they change
  behavior.

## Single Review Decision

Return exactly one top-level verdict:

```text
APPROVE IMPLEMENTATION
MODIFY IMPLEMENTATION
REJECT IMPLEMENTATION
```

The decision is whether this package can be used to run the registered formal
experiment and produce trustworthy evidence, after the specific corrections you
identify. `MODIFY` requires an enumerated, minimal, concrete correction list.

## Evidence Already Reproduced

All measured on the target commit, CUDA (RTX 4070, `torch 2.7.0+cu118`):

```text
7/7 focused tests pass in 60.35s
or_dum_no_op                     true
added parameters                 1608 per arm (DUM, EHC); 0 for OR
base optimizer parameters        15004 (= 14980 base + 24 W_z)
event optimizer parameters       1584 (= 176 event_head + 1408 mark_head)
DUM base zero-gradient count     [1,1,1,1] over four epochs
EHC base zero-gradient count     [0,0,0,0] over four epochs
event optimizer steps            DUM 4, EHC 4, OR 0
factor counts (smoke)            CREATE 4, KEEP 17, RENEW 9 -> categorical 26, mark 13
replay error, maximum            4.77e-7  (tolerance 1e-6)
checkpoint continuation          discrete/lifecycle/owned-RNG/global-RNG equal;
                                 continuous, model and optimizer errors all 0.0
per-update wall clock            OR 8.61s, DUM 8.14s, EHC 8.18s
```

Treat these as claims to be falsified, not as established facts. If an
invariant is satisfied by construction in a way the test cannot distinguish
from a genuine implementation, say so.

## Required Technical Review

Read `docs/project/IMPLEMENTATION_PLAN.md` as the contract and inspect every
location in `CODE_MAP.md`. Then decide the following rather than listing
options.

### 1. Treatment isolation

`primitive_logits = base_logits + W_z(m * stopgrad(z))`, `m=0` for `DUM`, `m=1`
for `EHC`, no bias for `OR`. Establish whether this is genuinely the **only**
arm-conditioned difference reaching sampling, storage, replay, loss, execution
and evaluation. A second implicit branch — an RNG consumption difference, a
control-flow divergence, a shape-dependent code path, a differing number of
kernel calls that perturbs a shared stream — would break attribution of `G` to
the commitment link. Search for one specifically.

### 2. The DUM control's validity

`DUM` must pay identical capacity, identical event learning and identical
optimizer exposure while having exactly zero primitive effect. Confirm the
zero-gradient argument holds for the entire run, not just at step 1: with input
exactly `0.0`, `W_z` gradients are zero, so Adam's first and second moments
stay at zero and the parameter never moves. State whether any path (weight
decay, gradient noise, `eps` handling, clipping, a non-zero `z` leak) could
move `DUM`'s `W_z` and thereby contaminate the control.

### 3. OR no-op equivalence

The `prepare_step` and logit-bias additions to `DirectPrimitiveARPolicy` must
leave the no-bias `OR` path bit-comparable to the pre-change learner in
parameters, state, actions, log probabilities, values, hidden transitions and
PPO algebra. Judge whether the implementation achieves this or merely passes a
test that samples too narrowly. `OR` is the standing access null; drift here
silently invalidates the comparator.

### 4. Lifecycle, clocks and censoring

Audit the five-step physical row order, `JOIN`/`CREATE` reset, temporary
leave/rejoin freeze-restore, the due-opportunity-before-rejoin-action rule,
`q` decrementing exactly once per active primitive action and never during
inactive time, forced `CLOSE` after the final reward, right-censoring of open
segments, and rollout-cutoff handling that must preserve state and bootstrap
without creating a synthetic event. Identify any ordering under which a segment
is double-counted, lost, or wrongly classified complete versus censored — this
directly biases the lifetime `CV` and bin statistics that gate the result.

### 5. Probability, replay and numerical stability

Verify factor support exactness (`CREATE` mark-only, `KEEP` categorical-only,
`RENEW` both, `CLOSE` none), the transformed-mark Jacobian
`2*(log2 - u - softplus(-2u))` including its behavior at large `|u|` where
`tanh` saturates, that replay recomputes from stored `u` rather than
resampling, and that detachment genuinely prevents gradient flow into either
head through `u`/`z`. Judge whether the `1e-6` replay tolerance is adequate in
`float32` for the registered 320,000-transition run, or whether error can
accumulate past it late in training.

### 6. Credit assignment

Every event row receives the same scalar advantage as the primitive action it
precedes. Assess whether this is the correct estimator given that an event may
precede a long segment of primitive actions, and whether it introduces bias
that would show up as an apparent `EHC` gain independent of the commitment
link. If you believe the credit rule is wrong, say so plainly — it is frozen in
the plan, but a genuine defect here would invalidate the experiment and is
exactly what this review is for.

### 7. Result contract soundness

Confirm the eight result branches are mutually exclusive under first-match
precedence at every boundary, including equality and intervals that straddle a
threshold, and that the "behavior confidently fails" dual (`UCB <= threshold`)
introduces no new threshold. Confirm the analyzer cannot select a successor,
change a threshold or perform a post-result rescue.

### 8. Test adequacy

Name the specific invariant a wrong implementation could violate while still
passing all seven focused tests. If you find one, give the concrete test that
should exist.

## Response Format

Use these exact sections:

1. **Verdict** — one of the three tokens above, on its own line.
2. **Blocking defects** — numbered, each with file, anchor, the invariant
   violated, and the minimal correction. Empty if none.
3. **Non-blocking findings** — same form, for issues that do not prevent the
   formal run.
4. **Falsified or unsupported claims** — any evidence item above you could not
   confirm from the code, and what would be needed to confirm it.
5. **Test gaps** — missing tests, most important first.
6. **Confidence** — what you inspected fully, what you sampled, and what you
   could not reach.

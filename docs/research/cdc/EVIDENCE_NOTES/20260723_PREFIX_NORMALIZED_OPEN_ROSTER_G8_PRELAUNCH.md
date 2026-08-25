# PREFIX_NORMALIZED_OPEN_ROSTER_G8 prelaunch acceptance

Date: 2026-07-23

```text
algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8
design=docs/research/designs/PREFIX_NORMALIZED_OPEN_ROSTER_G8.md
screen=logs/nonformal_scale_normalized_g8_screen_20260723_pm1/screen_result.json
exercise=logs/nonformal_open_roster_prefix_g8_20260723_pm1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=false
formal_compute_status=authorized_after_git_integration
conclusion_bearing_iteration_cost=0
iterations_remaining=9
```

## Code-side acceptance

- The active model adds one explicit `autoregressive_prefix` mode. Its default
  remains raw count and matches the closed G5 parameter state and shape.
- The selected mode divides raw action-prefix counts by total active N only at
  the actor inputs. Raw prefix counts remain in trajectory and replay evidence.
- Active member summation, the original count coordinate, environment
  observations, reward, task, lifecycle ownership, PPO, RNG, checkpoint and
  action factorization remain unchanged.
- Unselected mean-aggregation and bounded-count prototype branches are absent
  from the active source. The G7 module/runner/test are replaced rather than
  retained as a compatibility line.

Focused CPU one-thread tests pass `8/8`. The combined G8/G5 suite passes
`13/13`, including default-path equivalence, parameter-shape equality, prefix
replay, padding, G7 stress controls, lifecycle ownership, exact branch
boundaries, formal rejection and tamper negatives.

The bounded nonformal exercise completes one replicate, two updates, 11 cells
and all five domains. It is operationally valid, has finite learning, lifecycle
validity, replay maximum error zero, exact model immutability during evaluation,
12 constructive source-control profiles at utility one, and branch
`NONFORMAL_PREFIX_NORMALIZED_G8_EXERCISE_COMPLETE`. It is not formal evidence.

No advisory review was selected: the component choice followed the
pre-registered screen by a `0.0564` margin, the shared default path has a direct
regression, and no unresolved anomaly remains.

```text
pm_acceptance=FORMAL_READY_AFTER_GIT_INTEGRATION
next_boundary=PREFIX_NORMALIZED_OPEN_ROSTER_G8_FORMAL_ITERATION_9
```

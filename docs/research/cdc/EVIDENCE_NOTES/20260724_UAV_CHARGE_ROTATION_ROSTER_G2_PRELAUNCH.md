# UAV charge-rotation roster G2 prelaunch acceptance

Date: 2026-07-24

```text
source_family=UAV_CHARGE_ROTATION_ROSTER_G2
acceptance_owner=project_manager
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=false
conclusion_bearing=false
iterations_remaining=5
next_boundary=UAV_CHARGE_ROTATION_ROSTER_G2_FORMAL_ITERATION_23
```

## Decision

The frozen charge-rotation G2 source now has one executable active line. It is
independent of the closed temporary-loss G1 source: G1 remains
`SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1`, while G2 uses battery-driven
planned absence, deterministic station service and rejoin to create a distinct
load-bearing roster mechanism.

The implementation preserves the frozen energy profiles, lifecycle, policy
information sets, reward and utility, matched arms, PPO/replay semantics,
source-first ordering, seeds, budget, bootstrap, thresholds and seven-branch
precedence. Initial source pressure comes only from the RESET projection. Every
RESET/REJOIN projection must pass candidate, nearest-station, latest-safe,
current-only and lifecycle-plan checks. Replanning preserves already absent
owners and their station completion commitments.

## Proof-sized evidence

- Core tests: 22 passed.
- Runner tests: 20 passed.
- Integrated focused command: 42 passed on the registered CPU interpreter with
  one OMP/MKL thread.
- Fresh bounded run:
  `logs/nonformal_uav_charge_rotation_g2_cpu_20260724_pm2`.
- Operator terminal: train 0, evaluate 0, analyze 0.
- PM artifact validator: passed.
- Registered result:
  `NONFORMAL_UAV_CHARGE_ROTATION_G2_EXERCISE_COMPLETE`.
- Result flags: `operational_valid=true`, `formal=false`,
  `conclusion_bearing=false`.

The recovery tests cover truncated launch identity, source/evaluation/terminal
bindings, resume markers, final checkpoint markers and analysis-to-result
completion. Recovery never accepts a valid-but-wrong or tampered artifact.

## Scope closure

The earlier G1 runtime and tests are removed because its source and result are
already preserved by Git history, durable evidence and `docs/report/ITERATION_22.md`.
Scout inspection found no additional high-return, low-risk UAV infrastructure
hotspot after the accepted directional path-loss and first replay reuse. The
remaining nearest-station and small queue reductions are deliberately deferred
until profiling shows material cost.

This package is operational prelaunch evidence only and consumes zero
conclusion-bearing iterations. The next admissible action is the already
authorized formal CPU iteration 23 from the integrated source commit.

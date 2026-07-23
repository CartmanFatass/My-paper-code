# Ultra-scale open-roster G12 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=ULTRA_SCALE_OPEN_ROSTER_G12
implementation_status=PRELAUNCH_ACCEPTED_FORMAL_READY
design=docs/research/designs/ULTRA_SCALE_OPEN_ROSTER_G12.md
backend=cpu
torch_threads=1
formal_iteration=13
chain_iterations_remaining_before_run=5
```

## Goal

Determine whether the same frozen prefix-normalized G8 policy remains usable
when active roster size crosses the N=40 evidence boundary and reaches 48, 64
and 80 under the already established eight-edit churn mechanics.

## Task 1 - Define above-range profiles

Use capacities 64, 80 and 96 with maxima 48, 64 and 80. Retain the horizon,
wave source, membership-event transaction semantics and lifecycle ownership.
Each profile must be transition-valid and constructively attain utility one.

Focused proof: exact count schedules, eight events, expected/actual wave demand,
finite observations, lifecycle freeze/restore and constructive outcomes.

## Task 2 - Pair with frozen G8 finals

Import the exact three G8 terminal checkpoints with zero optimizer steps. Run
all three domains under deterministic and stochastic actions without modifying
policy state. Preserve the 128-episode G8 provenance while using 64 episodes per
new G12 cell.

Focused proof: checkpoint inventory, copy difference zero, immutable model,
complete 18-cell inventory and exact serialized arrays.

## Task 3 - Freeze conclusion semantics

Keep the absolute deterministic floor 0.90, minimum ultra replicate floor 0.85
and ultra stochastic floor 0.80. Apply the edge -> far -> ultra -> stability ->
success first-match order. Equality passes; the immediately lower float fails.
Formal token, counts, source commit and CPU runtime fail closed.

## Acceptance and launch

The G12 focused suite passes 5/5 and the G12 plus shared G5 suite passes 10/10.
The official bounded nonformal pipeline at
`logs/nonformal_ultra_scale_g12_20260723_pm1` is operationally valid with six
cells, 24 utility values, zero optimizer steps, exact checkpoint copy, immutable
model state and all source/lifecycle controls true. Nonformal evidence is not a
scientific result.

No additional review is selected because the new code is a thin profile and
contract specialization over the already accepted frozen-checkpoint core, and
focused evidence found no anomaly. Integrate, launch the exact formal commands
from the prelaunch note through the fixed operator, then independently close
the first-match branch.

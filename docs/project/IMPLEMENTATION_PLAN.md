# High-frequency roster churn G9 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=HIGH_FREQUENCY_ROSTER_CHURN_G9
implementation_status=FORMAL_CLOSED_ROBUST_HIGH_FREQUENCY_CHURN_G9
design=docs/research/designs/HIGH_FREQUENCY_ROSTER_CHURN_G9.md
backend=cpu
torch_threads=1
formal_iteration=10
chain_iterations_remaining_before_run=8
```

## Goal

Test whether the usable G8 prefix-normalized policy survives eight membership
edits, repeated absence/rejoin cycles and membership changes at short-wave
boundaries. This is a zero-training stress evaluation of frozen G8 finals, not
a new algorithm fit or a rescue of any closed result.

## Task 1 - Replace the completed G8 active line

Remove the G8-specific stress module, runner and test after preserving its
result in Git, reports and formal artifacts. Keep the shared
`DirectPrimitiveARPolicy(autoregressive_prefix="active_fraction")` implementation
as the active algorithm. Add only the three G9 churn profiles and their exact
lifecycle transition machinery.

Focused proof: simulate every transition; reject collisions and terminal
lifecycle reuse; require exact active-count schedules, post-event wave demand
and a constructive utility-one controller.

## Task 2 - Import, do not train

Require the exact successful G8 source, result branch, representation, CPU
runtime, counts and three update-250 final checkpoints. Copy those checkpoints
into a fresh G9 run root and require bitwise-identical model state. Record zero
optimizer steps.

Focused proof: repeated temporary absence freezes hidden state at every absent
step; rejoin restores it; genuine join starts from zero; terminal leave remains
inactive. Evaluation must not change model state.

## Task 3 - Freeze evidence and first-match semantics

Evaluate deterministic and stochastic policy behavior on `repeated_rejoin`,
`load_proximal` and `mixed_churn`, for exactly 18 formal cells. Validate exact
episode/profile inventories, source-control rows and serialized means. Apply
the frozen first-match order from the G9 design. Threshold equality passes and
the immediately lower floating-point value fails.

## Acceptance and formal launch

The G9 focused suite passes `6/6`; the combined G9 plus shared G5 regression
passes `11/11`. The official bounded nonformal CPU `train(import) -> evaluate ->
analyze` exercise at
`logs/nonformal_high_frequency_churn_g9_20260723_pm2` is operationally valid.
It records zero optimizer steps, exact checkpoint copying, three passing source
controls, six immutable evaluation cells and the required nonformal branch.

No advisory review is added because the focused reproducer, shared regression
and complete bounded path show no concrete anomaly. Integrate this accepted
source and assign the exact formal iteration-10 pipeline in the prelaunch note
to the fixed Luna-low operator.

The valid formal result consumes iteration 10 and leaves seven authorized
iterations. Operationally invalid evidence would have consumed none.

## Formal closure and successor

Source `ff7461fd2b0f3cfb7ad13a5f6f2730eb6bac3d99` completed all 18 registered
cells and returned `ROBUST_HIGH_FREQUENCY_CHURN_G9`. The three deterministic
CI95 lower bounds are `0.9309692`, `0.9294434` and `0.9299316`; mixed stochastic
mean is `0.9099933`. G9 is closed without rerun or tuning.

The next active boundary is zero-compute
`SCALE_CHURN_COMPOSITION_G10_DERIVATION`. This plan does not yet freeze its
large-count profiles or result gates.

# Direction-balanced full actor G30 formal result

```text
status=FORMAL_COMPLETE
operational_valid=true
iteration_consumed=true
iteration=20
source_commit=1e4fbb735107b2a924bb3fd4f682c251ab62fb72
branch=NO_DELAYED_ACCESS_DIRECTION_BALANCED_G30
next_boundary=G31_DELAYED_SPIKE_CREDIT_ALLOCATION_DERIVATION
```

The exact three-replicate CPU one-thread run closes six training rows, twelve
zero/final checkpoints and twenty-one evaluation cells. All source controls,
runtime identities, checkpoint bindings, replay/lifecycle/ownership invariants,
direction dots, composition identities and single Adam steps pass. The PM
independently recomputed the registered first-match branch.

G17 passes every compatibility gate: IID utility CI95 is
`[0.94011, 0.95000, 0.95634]`, held-out utility CI95 is
`[0.94011, 0.94442, 0.95089]`, gain CI95 is
`[0.33645, 0.39343, 0.44536]`, and the minimum episode is `0.89821`.
Minimum effort/mix correlations are `0.98445/0.99371`; maximum MAEs are
`0.02419/0.02093`.

G18 total utility, paired gain, rotating-member mechanism and replicate
stability pass. Their registered evidence is utility CI95
`[0.95872, 0.96449, 0.97364]`, gain CI95
`[0.23698, 0.24839, 0.26258]`, rotating-share CI95
`[0.87067, 0.88924, 0.90926]`, and minimum replicate utility `0.95870`.
The higher-precedence delayed-access gate fails because spike utility CI95 is
`[0.87611, 0.89346, 0.92093]`, below the frozen `0.90` lower-bound floor.

Per-replicate spike means are `0.87611`, `0.88323` and `0.92106`. Equal global
gradient directions therefore preserve immediate-task compatibility and learn
the broad delayed allocation, but do not make the load-bearing spike response
stable across fresh seeds. G30 is closed without seed, threshold, budget or UAV
rescue. The smallest next question isolates spike-credit allocation rather than
reopening general representation or source validity.

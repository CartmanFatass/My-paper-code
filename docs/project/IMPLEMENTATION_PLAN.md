# Prefix-normalized open-roster G8 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hashes are
> disabled.

```text
active_implementation=PREFIX_NORMALIZED_OPEN_ROSTER_G8
implementation_status=FORMAL_CLOSED_USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
design=docs/research/designs/PREFIX_NORMALIZED_OPEN_ROSTER_G8.md
backend=cpu
torch_threads=1
formal_iteration=9
chain_iterations_remaining_after_run=8
```

## Goal

Test the smallest representation repair selected after G7: normalize only the
autoregressive action prefix by active N, train from fresh seeds, and require
absolute usability from IID through the unchanged N=40 G7 stress domains.

## Task 1 - Keep only the selected algorithm

Parameterize the shared direct policy with `raw_count` and `active_fraction`
prefix modes. Preserve `raw_count` as the exact G5 default. The G8 active line
uses only `active_fraction`; remove the mean-aggregation and bounded-count
prototype branches after the nonformal screen.

Focused proof: default parameters and outputs retain G5 semantics; G8 keeps the
same parameter count; raw prefixes remain exact replay evidence while later
autoregressive inputs differ under fraction normalization.

## Task 2 - Replace G7 with one fresh-training G8 path

Replace the G7 module, runner and test rather than keeping adapters. Reuse its
seven stress profiles and the G5 training/held-out task. Train three fresh
replicates for 250 updates, with no G5 checkpoint resume. Evaluate zero joint
baselines and final deterministic/stochastic outcomes across five domains.

Focused proof: source controls cover 12 profiles; formal inventory is exactly
33 cells; checkpoints, representations, runtime, replay, lifecycle, outcome
arrays and evaluation immutability fail closed.

## Task 3 - Freeze result semantics

Use the first-match branch in the design: IID, held-out, moderate, far, joint,
learning gain, stability, then usable success. Each deterministic LCB floor is
0.90; joint minimum replicate is 0.85 and stochastic mean is 0.80. Threshold
boundary values pass and `nextafter` below fails.

## Acceptance and launch

Acceptance is complete. The G8 focused suite passes `8/8`; combined G8/G5
passes `13/13`. The nonformal full path at
`logs/nonformal_open_roster_prefix_g8_20260723_pm1` is operationally valid with
replay error zero, exact lifecycle/source controls, evaluation model drift zero
and the required nonformal branch. The earlier eight-variant screen selected
prefix-only normalization by a `0.0563965` minimum-domain margin.

After exact-path Git integration, assign one fresh formal
`train -> evaluate -> analyze` pipeline to the fixed Luna-low operator. A valid
result consumes iteration 9 and leaves eight authorized iterations.

## Formal closure and successor

Source `fcce714c296c55f3dcb5a0c0ee11090b393c26ba` completes all 33 cells and
returns `USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8`. The lowest deterministic
domain LCB is `0.9299927`, evaluation model drift is zero and joint learned-gain
LCB is `0.1707176`. G8 is closed without rerun or tuning.

The next active boundary is zero-compute
`HIGH_FREQUENCY_ROSTER_CHURN_G9_DERIVATION`; this G8 plan does not freeze its
event schedule or formal gates.

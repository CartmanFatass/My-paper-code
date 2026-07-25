# Runtime-capacity-invariant continuous roster G32 formal result

```text
iteration=24
algorithm=RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32
source_commit=fbce3609b11353634d1b4acb20cb27372de40bf2
run=logs/formal_runtime_capacity_g32_cpu_20260725_fbce360_r1
formal=true
conclusion_bearing=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
status=COMPLETE
operational_valid=true
operational_errors=[]
registered_branch=USABLE_RUNTIME_CAPACITY_G32
iteration_consumed=true
iterations_remaining=13
```

## Evidence closure

The registered experiment operator returned once at terminal completion.
Train, evaluate and analyze each exited zero. Their manifests bind to the same
integrated source commit, frozen formal authorization token, CPU runtime and
one-thread condition. Training contains three replicates and six zero/final
checkpoints. Evaluation contains 30 cells, 3,840 episode utilities, three exact
padding diagnostics and three mapping diagnostics. Evaluation uses zero
optimizer steps and preserves the evaluated state exactly.

All training updates are finite, all lifecycle contracts pass, and every
replicate has nonzero parameter and actor drift while the frozen residual output
remains exactly zero. The registered branch recomputed directly from the
analyzer predicate inputs is exactly `USABLE_RUNTIME_CAPACITY_G32`.

## Registered evidence

| Metric | Formal value |
|---|---:|
| capacity-8 utility CI95 | `[0.9502525, 0.9552011, 0.9590951]` |
| capacity-8 learned-gain CI95 | `[0.3465177, 0.5417124, 0.6643343]` |
| capacity-6 utility CI95 | `[0.9375735, 0.9435536, 0.9480192]` |
| capacity-12 utility CI95 | `[0.9483213, 0.9498142, 0.9512819]` |
| held-out gain CI95 | `[0.3658130, 0.5371965, 0.6471880]` |
| minimum held-out replicate | `0.9428362` |
| held-out stochastic mean | `0.8759143` |

The mapping correlations are all above `0.9898`, mapping MAEs are all below
`0.0166`, and the lifecycle gate passes. Across the paired cap8/cap12 process,
maximum observation, value, action, reward and hidden mismatches are all exactly
zero; lifecycle equality and inactive-padding-zero also pass.

## Mechanical disposition and scientific-review boundary

The registered analyzer branch is validly
`USABLE_RUNTIME_CAPACITY_G32`: under the frozen contract, the checkpoint's
parameters and behavior do not depend on configured maximum capacity across the
registered 6/8/12 family. This mechanical branch and its evidence cannot be
relabelled.

The result does not establish UAV transport, arbitrary capacities, or live
tensor-width changes inside one active trajectory. It does not retroactively
repair either source-non-identifiable UAV run. External Pro now owns the
scientific interpretation, CDC/portfolio update and next scientific action via
`FORMAL_RESULT_SCIENTIFIC_DISPOSITION`. Live runtime-capacity rebinding is a PM
code-side observation/candidate question, not an adopted successor unless Pro
selects it.

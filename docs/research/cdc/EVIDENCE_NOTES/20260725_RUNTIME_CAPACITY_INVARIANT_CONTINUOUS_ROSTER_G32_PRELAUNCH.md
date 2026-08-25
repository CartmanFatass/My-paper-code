# G32 runtime-capacity prelaunch acceptance

```text
boundary=RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32
evidence_kind=bounded_nonformal_prelaunch
formal=false
conclusion_bearing=false
iteration_cost=0
source_commit=fc0ca9dfb2a04e1a16ba7129b09914e6a4b8e676
run=logs/nonformal_runtime_capacity_g32_cpu_20260725_fc0ca9d_pm1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
result=NONFORMAL_RUNTIME_CAPACITY_G32_EXERCISE_COMPLETE
operational_valid=true
operational_errors=[]
pm_acceptance=accepted
next_boundary=RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_FORMAL_ITERATION_24
```

## Evidence closure

The registered experiment operator executed the integrated runner in the
foreground as three ordered stages. `train_manifest.json`,
`evaluation_manifest.json`, and `analysis_result.json` are all present and bind
to the same source commit. Train, evaluate and analyze exited successfully.
The runtime identity is CPU with one Torch thread.

The exercise contains one training replicate, ten evaluation cells, one
padding diagnostic and one mapping diagnostic. The analyzer reports
`status=COMPLETE`, `formal=false`, `operational_valid=true`, no operational
errors, and the registered nonformal branch. The exercise therefore proves the
executable evidence path, artifact closure and fail-closed analyzer wiring; it
does not estimate the formal result and consumes no scientific iteration.

## Preserved evidence contract

The formal contract remains exactly the one frozen in
`docs/research/designs/RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32.md`:
train only at runtime capacity 8, strict-load the same checkpoint without
optimizer steps at capacities 6, 8 and 12, and compare the exact paired
capacity-8/capacity-12 padding process. Seeds, budgets, thresholds, first-match
result precedence, replay tolerance, lifecycle and RNG ownership are unchanged.
The formal authorization token remains
`AUTHORIZE_RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_FORMAL_CPU_V1`.

Formal iteration 24 may start only from the integrated commit containing this
record, in a fresh run root, on the registered CPU-only interpreter with one
Torch thread. No UAV promotion is implied: G32 remains a toy-environment
mechanism-separation test.

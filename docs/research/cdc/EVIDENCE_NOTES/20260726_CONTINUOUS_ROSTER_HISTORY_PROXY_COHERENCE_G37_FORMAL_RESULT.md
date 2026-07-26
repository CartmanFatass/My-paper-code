# Continuous-roster history-proxy coherence G37 formal result

```text
iteration=28
algorithm=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0
source_commit=87f4dfbe56b36f31d34f134a3c350bd766fae8d7
run=logs/formal_continuous_roster_history_proxy_coherence_g37_cpu_20260726_87f4dfb_r1
formal=true
conclusion_bearing=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
schema_version=1
status=COMPLETE
operational_valid=true
operational_errors=[]
registered_branch=MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37
scientific_interpretation=pending_external_pro
iteration_consumed=true
iterations_remaining=9
```

## Mechanical evidence closure

The registered Experiment Operator held one foreground CPU-only workflow and
returned once after `evaluate:0` and `analyze:0`. No retry, resume, restart,
fallback, mixed backend or second formal run occurred. Serialized evaluation
and analysis times are `158.49333869999828` and `142.0982172999975` seconds,
totaling `300.5915559999958` seconds below the 28,800-second cap.

The frozen inventory is three replicates, capacities 6/8/12, four factorized
cells per replicate/capacity, 36 cells, 128 episodes per cell, 4,608 episodes,
221,184 real transitions, zero training transitions, zero optimizer steps and
10,000 paired hierarchical bootstrap resamples. `H=48`, `K_search=0`,
hypothetical transitions are zero, and nested rollout and replanning are false.
The exact formal G36 joint-donor artifact was read only and not rerun.

PM reread both terminal JSON artifacts and independently invoked the registered
validator. It strict-loaded the exact formal G35 CS final checkpoints and G36
joint-donor package; revalidated the serialized absolute preflight and its two
digests; checked donor support, factorized snapshot/permutation addressing,
fixed/random tape reuse, action-noise pairing, cell and episode inventories,
source signatures, lifecycle and complete 48-step traces; and returned no
artifact error. PM independently reproduced the registered first-match branch,
which equals the stored branch, and verified the evaluation-manifest digest
recorded by the analysis.

```text
preflight_evaluation_sha256=bdc1df5512cf532c7a2ea39acac9627fbf3461c48a77dfb345d16e4d19572f5c
preflight_analysis_sha256=bdc3bb5198a1e197ab7bed39e4c7eb406fbdde3606408d5ef61dc2ec0a66dfd4
g36_evaluation_sha256=03b6ae2bca6f284524b442bd642dd306b8a8db7e6103d177e6982bfeea864bf6
g36_analysis_sha256=0243133c102645f3310104f9b3371e21880714740ec9d8f7fa1527f38199b4ae
g37_evaluation_sha256=f4bc5657246bf16b29f03e3eb62b3e146781c15843110d7f0515f78bcb6f9fd2
g37_analysis_sha256=377e38f4e653de0ca6b33ba5c9086735668696a6a5134ff938e15e147f5ab233
```

## Registered analyzer inputs

`source_valid=true`, `g36_reference_valid=true`,
`factorized_access_pass=false`, `factorized_access_confident_fail=false`,
`coherence_noninferior=false` and `material_coherence_loss=false`.

| Quantity | Exact formal CI95 / value | Frozen decision use |
|---|---:|---:|
| fixed utility capacity 6 | `[0.9015744332211134, 0.9328779326558725, 0.9516143420116594]` | LCB `>=0.90` |
| fixed utility capacity 8 | `[0.8888933512782777, 0.9285765678508697, 0.9493234312590048]` | LCB `<0.90` |
| fixed utility capacity 12 | `[0.8891929680498273, 0.9272856483825807, 0.9468039473115082]` | LCB `<0.90` |
| random utility capacity 6 | `[0.900718475918172, 0.933511416719742, 0.9520219079665783]` | LCB `>=0.90` |
| random utility capacity 8 | `[0.8854879440814001, 0.9266266997866284, 0.9477917475728614]` | LCB `<0.90` |
| random utility capacity 12 | `[0.8905369829719556, 0.926921423495991, 0.9456838462139401]` | LCB `<0.90` |
| fixed stochastic pooled | `[0.8478731094483, 0.8732388599143639, 0.8866566905307084]` | LCB `>=0.80` |
| random stochastic pooled | `[0.8521280447443368, 0.8787163230467465, 0.8927749135770457]` | LCB `>=0.80` |
| minimum fixed deterministic replicate mean | `0.8929382811204333` | `>=0.85` |
| minimum random deterministic replicate mean | `0.8918815876579136` | `>=0.85` |
| primary joint-minus-factorized delta | `[0.006390570911043732, 0.021598878727825156, 0.05153553144695466]` | UCB `>0.05` |
| largest component joint-minus-factorized UCB | `0.09006605370262584` | diagnostic only under frozen selector |

Replaying the frozen selector reproduces:

```text
MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37
```

This note supplies mechanical evidence only. External Pro must provide the
scientific interpretation, exact retained/retired units, CDC edits and one next
action before successor work.

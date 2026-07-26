# Continuous-roster random-process G34 formal result

```text
iteration=25
algorithm=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34
source_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0
source_commit=15f95889f4a318905ba45a1977b5e9079d114545
run=logs/formal_continuous_roster_random_process_g34_cpu_20260726_15f9588_r1
checkpoint_root=logs/formal_runtime_capacity_g32_cpu_20260725_fbce360_r1
checkpoint_source_commit=fbce3609b11353634d1b4acb20cb27372de40bf2
formal=true
conclusion_bearing=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
schema_version=2
status=COMPLETE
operational_valid=true
operational_errors=[]
registered_branch=SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34
scientific_interpretation=SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CONTINUOUS_ROSTER_G34
iteration_consumed=true
iterations_remaining=12
```

## Mechanical evidence closure

The registered Experiment Operator held one foreground CPU-only run and
returned exactly once after `TRAIN:0`, `EVALUATE:0`, `ANALYZE:0`. Measured wall
time was 125.6 seconds and the process was no longer live. No retry, resume,
fallback or second run occurred.

Project Manager reread both terminal JSON artifacts and independently invoked
the accepted schema-2 artifact validator. It strict-loaded every declared G32
zero/final checkpoint for each replicate, kind and capacity; recomputed every
episode utility, minimum step, event window, process segment and roster
predicate from the serialized traces; and returned no artifact error.

The exact inventory is three replicates, capacities 6/8/12, 20 cells per
replicate, 60 cells total, 128 episodes per cell, 7,680 episodes and 368,640
real 48-step transitions. Every cell has zero optimizer steps and a valid
lifecycle. Every episode has one 48-step reward trace and one 48-step actual
roster-size trace. The artifact source commit, formal token, G32 checkpoint
source, CPU interpreter and one-thread runtime all match the registered
contract.

## Registered analyzer inputs

| Quantity | Exact formal value | Frozen gate |
|---|---:|---:|
| fixed utility CI95, capacity 6 | `[0.9383363581634688, 0.9433194447275682, 0.947577553429644]` | LCB `>= 0.90` |
| fixed utility CI95, capacity 8 | `[0.9506448167027731, 0.9553200045553776, 0.9590663265646272]` | LCB `>= 0.90` |
| fixed utility CI95, capacity 12 | `[0.9483330957430933, 0.9496359336804081, 0.9507117974263913]` | LCB `>= 0.90` |
| fixed stochastic pooled CI95 | `[0.87802084419575, 0.8804833490511034, 0.882489644339886]` | LCB `>= 0.80` |
| minimum fixed replicate mean | `0.9461977059101407` | `>= 0.85` |
| random utility CI95, capacity 6 | `[0.9424821662926387, 0.9472398478387709, 0.950811379488188]` | LCB `>= 0.90` |
| random utility CI95, capacity 8 | `[0.949381716985598, 0.9530597837954824, 0.9558494949576671]` | LCB `>= 0.90` |
| random utility CI95, capacity 12 | `[0.9437868293824532, 0.9465002907377293, 0.9491012131131338]` | LCB `>= 0.90` |
| random event-window CI95, capacity 6 | `[0.9113084501920862, 0.9144554734912054, 0.9176715495531846]` | LCB `>= 0.85` |
| random event-window CI95, capacity 8 | `[0.9279652381497298, 0.9336407364585912, 0.9387059297865529]` | LCB `>= 0.85` |
| random event-window CI95, capacity 12 | `[0.9153626442670233, 0.920317534236152, 0.9244311031934429]` | LCB `>= 0.85` |
| random process-segment CI95, capacity 6 | `[0.9148101402545669, 0.9174186809757666, 0.9201248060434315]` | LCB `>= 0.85` |
| random process-segment CI95, capacity 8 | `[0.9287942148316672, 0.9328581180842299, 0.9372952897236051]` | LCB `>= 0.85` |
| random process-segment CI95, capacity 12 | `[0.9127466268729552, 0.9198902644411329, 0.92589820373566]` | LCB `>= 0.85` |
| random-minus-fixed CI95, capacity 6 | `[0.0027178845167742166, 0.003906953423668727, 0.005021409254273975]` | LCB `>= -0.05` |
| random-minus-fixed CI95, capacity 8 | `[-0.0034914787324839417, -0.0022167292500844247, -0.0011482458344912836]` | LCB `>= -0.05` |
| random-minus-fixed CI95, capacity 12 | `[-0.0050676247540788226, -0.0031544836148483073, -0.0008543044261393424]` | LCB `>= -0.05` |
| learned-gain CI95 | `[0.3483684792766632, 0.5380063244575051, 0.6698512887526746]` | LCB `> 0` |
| random stochastic pooled CI95 | `[0.8831535155291594, 0.8859851010432778, 0.8893205464580397]` | LCB `>= 0.80` |
| minimum random replicate mean | `0.9469120055664803` | `>= 0.85` |

The constructive source and source-structure predicates are true. Fixed and
random primary gates pass; neither registered confident-fail predicate fires.
The capacity-8 time-rotation annotation is `LOAD_BEARING`, with utility CI95
`[0.8917173586289644, 0.8949441603646315, 0.8972918511177238]` and
control-minus-primary CI95
`[-0.05961515933181619, -0.058076318438105484, -0.05675347876528668]`.
The reactive-ablation annotation is `UNDERPOWERED`, with utility CI95
`[0.846098438340096, 0.886360242226113, 0.9138471740460744]` and
control-minus-primary CI95
`[-0.1078219816279635, -0.06660456558471971, -0.042005741479727354]`.
Both remain non-rescuing annotations under the frozen branch semantics.

## Mechanical disposition and scientific-review boundary

Project Manager reproduced the registered first-match selector directly from
the analyzer predicate inputs. Its result equals the stored branch exactly:

```text
SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34
```

This valid registered branch consumes conclusion-bearing iteration 25 and
cannot be relabelled. External Pro accepted the scientific disposition as:

```text
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CONTINUOUS_ROSTER_G34
```

G34 adds zero-shot transport from G32's fixed 12/24/36 three-event schedule to
the exact bounded P0 random four-event family at configured capacities 6/8/12.
It retires dependence on that exact schedule and atomic R+J inside P0, but not
arbitrary process-law dependence. The true-time rotation is load-bearing for
the exact checkpoint; the reactive ablation is underpowered. Neither selects
recurrence or G31-credit necessity.

The binding next action is the zero-compute
`CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT`. It must freeze
a fresh paired recurrent versus current-state/feedforward comparison that holds
information, true time, age, previous action, G31 credit, capacity, interaction,
optimizer exposure and parameter matching fixed. No implementation or compute
is authorized by this result disposition.

# Continuous-roster reactive-reduction G35 formal result

```text
iteration=26
algorithm=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35
source_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0
source_commit=f626dfd8a345ef670e08e601344b67e28ffb3563
run=logs/formal_continuous_roster_reactive_reduction_g35_cpu_20260726_f626dfd_r1
formal=true
conclusion_bearing=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
schema_version=2
status=COMPLETE
operational_valid=true
operational_errors=[]
registered_branch=CURRENT_STATE_REDUCTION_SUFFICIENT_G35
scientific_interpretation=SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CURRENT_STATE_CONTINUOUS_ROSTER_G35
iteration_consumed=true
iterations_remaining=11
```

## Mechanical evidence closure

The registered Experiment Operator held one foreground CPU-only run and
returned exactly once after `train:0`, `evaluate:0`, `analyze:0`. No retry,
resume, fallback, mixed backend or second run occurred. The serialized stage
times are 1,856.051237 seconds for training, 173.446424 seconds for evaluation
and 10.216002 seconds for analysis, a 2,039.713663-second sum below the frozen
28,800-second formal cap.

Project Manager reread all three terminal JSON artifacts and independently
invoked the accepted schema-2 artifact validator. It strict-loaded every fresh
REC/CS zero and final checkpoint, rechecked the matched-parameter and exposure
contracts, recomputed every utility, event-window, process-segment and roster
predicate from the serialized traces, and returned no artifact error. The
stored training and evaluation digests were reproduced exactly as
`30c6e75095502e9983c3c8e30b40c335e2304817b3fbc798c4798a58d15ca067`
and `fee215d449bb2a20609717864129b9df3631f0677637f4482e1e85e2685810fe`.

The frozen inventory is three replicates, two arms, 99 evaluation cells,
12,672 evaluation episodes, 460,800 training transitions, 608,256 evaluation
transitions, 1,069,056 real transitions total and 3,600 training optimizer
steps. Evaluation has zero optimizer steps. Intrinsic search `K=0`,
hypothetical transitions are zero, and nested rollout and replanning are false.

## Registered analyzer inputs

Both arms pass the frozen common access gates. The constructive source and all
lifecycle predicates are valid; neither access-confident-fail predicate fires.

| Quantity | Exact formal value | Frozen decision use |
|---|---:|---:|
| CS access pass | `true` | common gate |
| REC access pass | `true` | common gate |
| REC-minus-CS pooled CI95 | `[-0.017350521583833534, -0.008121271564817265, 0.0007129542703793057]` | UCB `<= 0.05` for CS-sufficient branch |
| REC-minus-CS capacity-6 CI95 | `[-0.014529841039829237, -0.010553569981652001, -0.006640444328665082]` | UCB `<= 0.05` |
| REC-minus-CS capacity-8 CI95 | `[-0.019335595315538797, -0.008653537689269672, 0.0030352695674895655]` | UCB `<= 0.05` |
| REC-minus-CS capacity-12 CI95 | `[-0.018001666557650613, -0.0052485529970797, 0.005408241068281625]` | UCB `<= 0.05` |
| CS random stochastic pooled CI95 | `[0.882876931834044, 0.8916826436134186, 0.896790909706548]` | access floor LCB `>= 0.80` |
| REC random stochastic pooled CI95 | `[0.8778201291671167, 0.8829304870942118, 0.8891270533961136]` | access floor LCB `>= 0.80` |
| CS learned-gain CI95 | `[0.2712661774442219, 0.28485037597269725, 0.29464389080684883]` | strict LCB `> 0` |
| REC learned-gain CI95 | `[0.27393238405004244, 0.29580966885458015, 0.3360981433700915]` | strict LCB `> 0` |
| minimum CS random deterministic replicate mean | `0.9410286758828444` | `>= 0.85` |
| minimum REC random deterministic replicate mean | `0.9393195124442184` | `>= 0.85` |

`current_state_sufficient=true` and `recurrent_advantage=false`. Replaying the
frozen first-match selector from these predicate inputs reproduces the stored
branch exactly:

```text
CURRENT_STATE_REDUCTION_SUFFICIENT_G35
```

## External Pro scientific disposition

External Pro accepted the registered branch unchanged and supplied the binding
scientific disposition:

```text
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CURRENT_STATE_CONTINUOUS_ROSTER_G35
```

Inside exact G35-P0, a freshly trained fully informed actor with zero learned
cross-step or cross-lifecycle carry is sufficient under the registered access
contract and noninferior to the matched REC arm by the frozen 0.05 margin. This
retires only the proposition that learned per-lifecycle actor carry is required
for access or supplies a material finite-budget advantage greater than 0.05 in
this source. The pooled interval still crosses zero, so it does not establish
overall CS superiority at 95% confidence; only capacity 6 has an entirely
negative interval.

The result does not retire recurrence globally. G35 retains true normalized
time, lifecycle age, previous actions, current load and target mix, active-set
aggregation, the autoregressive prefix, centralized critic and G31 credit. It
does not identify whether those history proxies or the credit estimator are
necessary, and it supplies no arbitrary-capacity, process, horizon or UAV
claim.

The binding next action is the zero-compute design audit:

```text
CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_DESIGN_ASSERTION_AUDIT
```

It must freeze a zero-training paired evaluation of the exact formal G35 CS
final checkpoints under registered execution versus an actor-only intervention
that destroys the history information in true time, lifecycle age and both
previous-action coordinates while retaining all current load/mix, capability,
active-set, prefix, critic, source, checkpoint and action-stream facts. G33
remains abandoned and cannot be reactivated.

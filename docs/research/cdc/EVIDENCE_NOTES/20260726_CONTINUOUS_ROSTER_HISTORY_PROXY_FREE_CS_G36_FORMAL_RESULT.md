# Continuous-roster history-proxy-free CS G36 formal result

```text
iteration=27
algorithm=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0
source_commit=8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04
run=logs/formal_continuous_roster_history_proxy_free_cs_g36_cpu_20260726_8f1cd60_r1
formal=true
conclusion_bearing=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
schema_version=1
status=COMPLETE
operational_valid=true
operational_errors=[]
registered_branch=HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36
scientific_interpretation=SUPPORTED_RETAINED_BOUNDED_ACTUAL_HISTORY_SENSOR_BUNDLE_SUBSTITUTION_G36
iteration_consumed=true
iterations_remaining=10
```

## Mechanical evidence closure

The registered Experiment Operator held one foreground CPU-only workflow and
returned once after `train_validation:0`, `evaluate:0`, `analyze:0`. The train
phase only validated the frozen zero-training inventory. No retry, resume,
restart, fallback, mixed backend or second formal run occurred. Serialized
evaluation and analysis times are `102.56485599999905` and
`65.39992729999904` seconds, totaling `167.964783299998` seconds below the
28,800-second cap.

The frozen inventory is three replicates, capacities 6/8/12, four intervention
cells per replicate/capacity, 36 cells, 128 episodes per cell, 4,608 episodes,
221,184 real transitions, zero training transitions, zero optimizer steps and
10,000 paired hierarchical bootstrap resamples. `H=48`, `K_search=0`,
hypothetical transitions are zero, and nested rollout and replanning are false.

PM reread both terminal JSON artifacts and independently invoked the registered
validator. It strict-loaded the exact formal G35 package and CS final
checkpoints; revalidated the serialized absolute preflight and both preflight
digests; checked donor support, zero history-read and checkpoint-update
counters, paired proxy/action digests, cell and episode inventories, source
signatures, lifecycle and 48-step traces; and returned no artifact error. PM
then independently regenerated the 10,000-resample plan, all access and paired
contrasts, the complete metrics object and the first-match branch. They match
the stored analysis exactly.

```text
preflight_evaluation_sha256=8f7397f384a2e0d97fa8842f8555f9530eb1831276882def07f74619d4498223
preflight_analysis_sha256=e6f5a670a27f4ddc4418c602adc6f8b955a024bd380ece4c4b29f8dc3e9f4d7c
g35_training_sha256=30c6e75095502e9983c3c8e30b40c335e2304817b3fbc798c4798a58d15ca067
g35_evaluation_sha256=fee215d449bb2a20609717864129b9df3631f0677637f4482e1e85e2685810fe
g35_analysis_sha256=ed8a4559592b023ab617cddb86ee188a67098c3f72830f206a13b4539799adfa
g36_evaluation_sha256=03b6ae2bca6f284524b442bd642dd306b8a8db7e6103d177e6982bfeea864bf6
```

## Registered analyzer inputs

`registered_source_access_valid=true`, `intervention_access_pass=true`,
`intervention_access_confident_fail=false`, `proxy_noninferior=true` and
`material_proxy_loss=false`.

| Quantity | Exact formal CI95 / value | Frozen decision use |
|---|---:|---:|
| fixed utility capacity 6 | `[0.9476289772582395, 0.9513876434241881, 0.9567182034506132]` | LCB `>=0.90` |
| fixed utility capacity 8 | `[0.9487348354206456, 0.953464095576792, 0.9567208196108495]` | LCB `>=0.90` |
| fixed utility capacity 12 | `[0.9320951897781492, 0.9454222123385213, 0.9529370436139648]` | LCB `>=0.90` |
| random utility capacity 6 | `[0.950706320997303, 0.9538494370677635, 0.9580481864084935]` | LCB `>=0.90` |
| random utility capacity 8 | `[0.9496175958361806, 0.9533748712743214, 0.9561255617255664]` | LCB `>=0.90` |
| random utility capacity 12 | `[0.93111778273711, 0.944510936917827, 0.9519477751934515]` | LCB `>=0.90` |
| fixed stochastic pooled | `[0.8773655367335621, 0.8849651174297508, 0.889511767008549]` | LCB `>=0.80` |
| random stochastic pooled | `[0.8835508009460661, 0.8912698785527424, 0.8959985625906101]` | LCB `>=0.80` |
| minimum fixed deterministic replicate mean | `0.9426373792427989` | `>=0.85` |
| minimum random deterministic replicate mean | `0.9436276918922709` | `>=0.85` |
| primary registered-minus-intervention delta | `[-0.0024789536237496625, 0.00010478693310413677, 0.0035748522602639253]` | UCB `<=0.05` |
| largest deterministic utility delta UCB | `0.007528676553502345` | `<=0.05` |
| largest event/segment delta UCB | `0.005265931579435489` | `<=0.05` |
| fixed stochastic delta UCB | `0.001926237552798347` | `<=0.05` |
| random stochastic delta UCB | `0.002033074794524479` | `<=0.05` |

Replaying the frozen selector reproduces:

```text
HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36
```

## External Pro scientific disposition

External Pro accepted the registered branch without modification as
`SUPPORTED_RETAINED_BOUNDED_ACTUAL_HISTORY_SENSOR_BUNDLE_SUBSTITUTION_G36`.
For the exact formal G35 CS final checkpoints and registered G32/G34-P0 family,
the actor's actual true-time, lifecycle-age and two previous-action sensors may
be replaced by the frozen active-count-conditioned source-valid donor bundle
while retaining all access gates and noninferiority by the frozen 0.05 margin.

This is sensor substitution, not architectural deletion: four history-shaped
coordinates, the exact donor law and its internal joint coherence, active masks,
lifecycle ownership, critic true time and G31 training provenance remain. The
smallest retired unit is the necessity or >0.05 material benefit of acquiring
the target episode's actual coherent four-field history bundle for those exact
checkpoints. The unique successor is
`CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT`.

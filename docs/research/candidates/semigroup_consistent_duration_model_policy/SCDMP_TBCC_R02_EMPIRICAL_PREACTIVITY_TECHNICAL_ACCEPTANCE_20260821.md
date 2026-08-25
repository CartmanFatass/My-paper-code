# SCDMP TBCC revision 02 empirical preactivity technical acceptance

```text
document_kind=cm_empirical_preactivity_technical_acceptance
direction_id=semigroup_consistent_duration_model_policy
science_revision=SCDMP-TBCC-ORDER-VALUE-SCIENCE-20260821-02
empirical_stage=SCDMP-TBCC-R02-FULL-EMPIRICAL-PANEL
cm_owner=CM_semigroup_consistent_duration_model_policy
preactivity_technical_acceptance=accepted
fresh_coordinate_materialized=false
master_present=false
empirical_activity_started=false
root_lease_issued=false
question_relevant_output=none
```

## Decision

The ABI2 native-first production source set, prerequisite-dependent runner,
training/evaluation/analyzer services, create-only resumable frontier and
corrected result-blind production-chain efficiency evidence are technically
accepted for preactivity.

The object may enter the next exact boundary: one fresh disjoint blinded master
and coordinate-family binding, followed by an Operational-Root-issued
direction-scoped CPU lease. Neither action occurred in this acceptance turn.
The runner must remain unopened until the fresh binding is installed and the
exact Root lease validates against it.

There is no science ambiguity or material resource-class expansion. The formal
production runner remains unexecuted by design; complete formal execution is
the later leased activity, not a missing preactivity gate.

## Frozen artifacts

- Source manifest:
  `artifacts/scdmp_tbcc_r02_full_empirical_20260821/empirical_source_manifest.json`
  with SHA-256
  `69f8f3694cbaaa811eab9f0b1ade3ebda8dc52b0a72abd87bb3cbe6669acd047`.
- Identity-free CM acceptance:
  `artifacts/scdmp_tbcc_r02_full_empirical_20260821/CM_PREACTIVITY_ACCEPTANCE.json`
  with canonical-byte SHA-256
  `d788df73063e03aadf13b3b1e13f7069912046e00e8c8326315723fe9d467333`.
- Corrected production-chain benchmark:
  `runtime/benchmarks/scdmp_tbcc_r02_production_preactivity_20260821.json`
  with SHA-256
  `e51917952a45e03ee1897700c12e25c990e1b4e8a0737989bcfa143adde9e8e4`.
- Exact unmaterialized coordinate proposal is embedded in the CM acceptance;
  `materialized=false`, `master_present=false`, no sampled words or coordinate
  rows exist.

The identity-free foreground preflight validated the live source manifest,
all three shared widths 12/120/144, ABI2 reward-trace receipt, acceptance and
future output paths. Its bindings are:

```text
source_manifest_sha256=69f8f3694cbaaa811eab9f0b1ade3ebda8dc52b0a72abd87bb3cbe6669acd047
preactivity_acceptance_sha256=d788df73063e03aadf13b3b1e13f7069912046e00e8c8326315723fe9d467333
native_binding_sha256=11876d25a0f5eb7b5c94bb51a9482c8c9f31dbe64dc48ed4d7ba6e22c27cea56
materialized=false
master_present=false
scientific_activity_started=false
```

## ABI2 and native-only production binding

The accepted shared component remains
`scdmp.tbcc_order_value.r02.full_host`, with production widths exactly
`8,12,32,120,144`; width 1 is conformance-only and shared widths 1/2 fail
before load.

```text
abi=2
magic=6071489204069610049
native_source_sha256=ea2149b187ba65c9229f0ada9c3bd55bd0f424ec5a5830de1f454585b488de38
build_key=9a9801e94e1b02468df1e3d59e0c0055b85e2d02306c018bb275b69e0f718fe3
dll_sha256=df1097603c3fd2e1f66875e5d3209fcc509609f870569a205efc83c607a7bb9d
dll_bytes=177664
host_output_bytes=336
primitive_reward_trace_capacity=13
full_reset_step_cpp=true
python_fallback=false
```

The C++ host produces each renewal's exact primitive reward trace with
`count=ticks_advanced`, a finite active prefix, canonical zero tail and prefix-
sum consistency. Production training consumes only this trace. Python plant or
reward reconstruction is absent and forbidden.

## Runner, frontier and analyzer acceptance

The foreground runner validates manifest, preactivity acceptance, output paths,
Root lease/argv/resources and live native receipt before DPAPI unseal, model
construction, native access or frontier mutation. It uses one Torch thread per
worker and only the registered native widths.

The realized path is fixed and nonadaptive:

1. exactly 24 foundation update-160 finals and the complete foundation
   competence gate;
2. only after a pass, the exact 18-action/four-tape/paired-graph opportunity
   panel and atomic `Q/D/S` gate;
3. only after both passes, exactly 72 TREAT/FREE/SET update-96 finals and the
   complete five-controller final evaluation; and
4. exactly one complete first-true result for the realized prerequisite path.

The frontier binds source/card/shared/native/coordinate/master/origin lineage,
uses create-only hash-linked generations, preserves same-coordinate resume and
rejects gaps, duplicates, tampering, path escape and cross-lineage reuse.
Intermediate checkpoints and gates are blinded mechanical state. Only the
complete realized-path result can cross the Root boundary; partial cells,
per-action values, training curves and intermediate inference are not exposed.

The analyzer implements the complete foundation competence family, exact
Stage-1b opportunity analyzer, five-controller direct endpoint families,
strict margins and exhaustive first-true branch map without changing any card
threshold, action, tape, seed, budget, checkpoint schedule or controller.

## Corrected production-chain efficiency acceptance

```text
chain_coverage=environment|loader|batch|forward_backward|rollout|evaluation|io|resume
efficiency_review=COMPLETE
production_runner_formally_executed=false
scientific_activity=false
```

The corrected record includes exact process-cold/warm ABI2 loading, native
widths 12/120/144, batched model forward/backward/AdamW, ABI2 rollout reward
trace, evaluation/analyzer adapters, checkpoint/frontier/gate/result atomic
I/O, cold resume and the actual production ThreadPool topology.

It accounts for all `10,752` update generations plus `96` initial frontiers:

```text
foundation_generations=24*160=3840
treat_generations=24*96=2304
free_generations=24*96=2304
set_generations=24*96=2304
initial_frontiers=96
projected_storage_bytes=2501647699
projected_storage_gib=2.3298409758
worst_resume_wall_seconds=40.44717
```

The 4 GiB durable-storage fence passes. Projected serial I/O includes checkpoint
binary, receipt, frontier, gate/result shapes and one worst resume; serial
preflight/analyzer/I/O/resume costs are not divided by worker speedup.

The concurrency measurement calls the actual production
`production._parallel_ordered` ThreadPool path with disjoint unique ordinals at
1/2/4 workers. Every topology reconstructs the same model/optimizer/frontier/
native-endpoint proof digest. The selected measured four-thread speedup is
`1.1521762556x`; the old subprocess speedup is explicitly excluded from
acceptance use.

The exact complete-work projection is:

```text
cpu_core_hours=2.84042
four_worker_wall_hours=2.47524
peak_rss_bytes=312471552
storage_bytes=2501647699
dominant_bottleneck=production_training_orchestration
kernel_double_counting=false
resource_class_remains_credible=true
```

This remains below the frozen conservative authority of 80--240 CPU
core-hours, 24--72 four-worker hours, 12/20 GiB RAM, 10 GiB scratch and 4 GiB
durable storage. A focused reviewer confirmed that the corrected record closed
the generation-retention/I/O and actual-thread-topology findings, with no
remaining Critical/High/Medium defect.

## Validation and remaining boundary

The current TBCC suite passed `107` checks with the required interpreter and
isolated `--basetemp`. Source-manifest reconstruction, live ABI2 shared guard,
canonical acceptance validation and identity-free CLI preflight also passed.

Remaining unknown: only formal production performance and the realized
scientific prerequisite path, both intentionally unobserved until later leased
execution. This uncertainty does not block fresh-coordinate and lease
readiness because the complete source, counts, resource ceiling, resume and
fail-closed paths are frozen and accepted.

## Semantic boundary

```text
observed_fact=abi2_native_first_runner_analyzer_frontier_source_manifest_and_corrected_full_chain_efficiency_are_preactivity_accepted
local_action_fence=no_master_identity_coordinate_binding_model_checkpoint_training_evaluation_result_lease_or_activity_in_this_acceptance_turn
scientific_stage_continuation=one_fresh_disjoint_blinded_coordinate_family_then_root_direction_scoped_cpu_lease_and_one_complete_prerequisite_dependent_atomic_panel
continuation_owner=operational_root_and_same_direction_cm_under_the_applied_empirical_envelope
root_decision_class=fresh_coordinate_then_lease_resource_decision
does_not_imply=scientific_result|partial_interpretation|stage_b|old_object_reuse|search|second_surface|deployment|flight
```

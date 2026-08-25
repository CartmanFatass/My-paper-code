# MGTAP preactivity resource-estimate intake

```text
direction_id=metric_ground_transport_allocation
logical_identity=EM-metric_ground_transport_allocation
generation=2
intake_kind=non_scientific_preactivity_resource_report
owner=EM
engineering_handoff=8627c32
engineering_state_revision=7
engineering_state_sha256=9f84479c975a6689d11434f1dd5a7397e2b81b00efa1ca367ce6190ef27ef534
manifest_sha256=795aa6b11fe0ddd2aa95ccd11bc655e11bb79c786832ea6c0e79155ab51a3b87
resource_estimate_sha256=0cedd7679976b6ccdc1b1eb52440acdb1bf3d425e6ce5ba33acf6eca195e27b6
scientific_result=false
efficacy_interpretation=false
successor_command_authorized=false
next_owner=EM
next_queue=FREEZE_TERMINAL_SUCCESSOR_AUTHORITY
```

## Controlling boundary

This intake closes only the explicit preactivity resource-estimation request in `MGTAP_MATCHED_UPDATE_SUPPORT_IDENTIFIABILITY_RESOURCE_HANDOFF_20260825.md`. It does not change the accepted bounded structural nonidentification of revision 04, inspect or reinterpret a scientific efficacy result, alter the prospective matched update-time-support discriminator, authorize a successor command, or supply the still-missing successor authority, fresh seed namespace, gate-failure artifact schema, or mathematical closure.

## Provenance validation

The exact references in the Root wake and engineering state revision 7 agree:

| Object | Exact reference |
| --- | --- |
| Engineering state | `docs/research/candidates/metric_ground_transport_allocation/workflow/engineering/state.json`, SHA-256 `9f84479c975a6689d11434f1dd5a7397e2b81b00efa1ca367ce6190ef27ef534` |
| Terminal manifest | `temp/directions/metric_ground_transport_allocation/exp/mgtap-preactivity-resource-estimate-20260825/manifest.json`, SHA-256 `795aa6b11fe0ddd2aa95ccd11bc655e11bb79c786832ea6c0e79155ab51a3b87` |
| Resource report | `temp/directions/metric_ground_transport_allocation/exp/mgtap-preactivity-resource-estimate-20260825/resource-estimate.json`, SHA-256 `0cedd7679976b6ccdc1b1eb52440acdb1bf3d425e6ce5ba33acf6eca195e27b6` |

The manifest binds direction `metric_ground_transport_allocation`, assignment `MGTAP-Preactivity-Resource-Estimate-20260825`, run `mgtap-preactivity-resource-estimate-20260825`, operator `Operator-mgtap-preactivity-resource-estimate-20260825`, code SHA `898c95025e572b2c0c50d09601dde68d905e6285`, and command SHA-256 `eec09ab5427ef9c6101e762d4dcbd1a640d315193072d4daa7776d1f811ccbcf`. Its exact command output path is the resource-report path above. The process is terminal `SUCCEEDED`, exit code `0`, terminal reason `CHILD_EXIT_0`, and `group_quiescent=true`; the manifest records one worker, four threads, zero captured environment variables, and `memory_safe=true`.

The report identifies itself as `mgtap_non_scientific_preactivity_resource_estimate`, binds Linux WSL2, CPython 3.12.3, NumPy 1.26.3, Torch 2.7.0 CPU, one process, four intra-op threads, one inter-op thread, and zero accelerators. It contains resource fixtures and projections, not MGTAP reward, calibration, stationarity, coupling, interval, or efficacy output. Provenance is therefore coherent with the authorized non-scientific estimator boundary.

## Absolute resource intake

### Conditional all-pass path

| Quantity | Central estimate | Conservative upper | Classification |
| --- | ---: | ---: | --- |
| Wall time | `94.56295605390551 s` | `228.95354024894573 s` | `at_or_below_7200_seconds` |
| Process CPU time | `94.24349612399436 s` | `268.26531733124534 s` | grounded |
| Peak RSS | `451,526,656 B` | `541,831,988 B` | within safe capacity and source envelope |
| Temporary storage | `1,760,862,176 B` | `2,201,077,720 B` | within safe capacity and source envelope |
| Retained storage | `1,760,862,176 B` | `1,936,948,394 B` | within safe capacity and source envelope |
| Processes / threads / accelerators | `1 / 4 / 0` | `1 / 4 / 0` | grounded |

The comparison capacities are `10,494,004,428 B` safely available memory and the `4,294,967,296 B` source RSS envelope; `803,456,437,452 B` safely available disk and the `8,589,934,592 B` source disk envelope. The all-pass conservative upper is below both capacity pairs.

### Gate-only termination path

| Quantity | Central estimate | Conservative upper | Classification |
| --- | ---: | ---: | --- |
| Wall time | `27.411457927693846 s` | `80.37234768758935 s` | grounded |
| Process CPU time | `27.30201254399759 s` | `97.68308711999799 s` | grounded |
| Peak RSS | `230,957,056 B` | `277,148,468 B` | within safe capacity and source envelope |
| Temporary storage | unknown | unknown | no terminal gate-failure storage schema |
| Retained storage | unknown | unknown | no terminal gate-failure storage schema |
| Processes / threads / accelerators | `1 / 4 / 0` | `1 / 4 / 0` | grounded |

The missing gate-only disk values are not an estimator defect. The controlling audit already identified the absence of a prospective calibration-terminal tree/manifest. Defining that schema is EM science-authority preparation before production construction; the estimator correctly retained the quantity as unknown rather than inventing bytes.

## Resource classification

1. The all-pass conservative wall estimate is `228.95354024894573 s`, below `7,200 s`. On this resource report, a later exact command does not require a performance-reasonableness review attempt or explicit user approval for duration.
2. The all-pass conservative RSS estimate is `541,831,988 B`, below both safe available memory and the source envelope. No reduction, batching, or sharding is required by this estimate.
3. The all-pass conservative temporary/retained disk estimates are below both safe available disk and the source envelope.
4. The estimator reports `explicit_user_approval_required=false`, `performance_reasonableness_review_attempt_required=false`, `reduction_batching_or_sharding_required=false`, and `self_authorized=false`.
5. `self_authorized=false` controls: favorable resources do not create scientific authority, mathematical closure, an engineering construction request, an Operator lease, or permission to launch the prospective command.

There is no observed estimator defect requiring a CM return. The exact requested resource quantities are grounded for the all-pass path, while the sole unknown is correctly traced to a missing scientific gate-failure storage contract.

## Owner and queue decision

The next owner is **EM**, not Root scheduling/user approval, CM defect repair, or Experiment Operator:

- **Not Root approval/scheduling:** the conservative wall, memory, and disk estimates do not cross an approval or safety boundary. Root retains lifecycle sequencing but has no resource exception to adjudicate now.
- **Not CM:** the report is terminal, provenance-coherent, and classification-complete for the all-pass path; gate-only disk is blocked by missing science, not estimator behavior.
- **Not Experiment Operator:** no successor command is scientifically complete or authorized.
- **EM:** the next bounded queue is `FREEZE_TERMINAL_SUCCESSOR_AUTHORITY`: author the complete matched update-time-support successor, literal fresh seeds and namespace, universal `V256/V224` gate, calibration-terminal artifact schema and work counts, then prepare fresh same-conversation mathematical closure. That work requires a later explicit EM wake and is not performed in this intake.

## No-action record

This intake launched no command, read no scientific result or partial-value output, contacted no provider, changed no source/test/Portfolio/registry/runtime/Git authority, and dispatched no CM or Experiment Operator. It promotes only the terminal non-scientific resource classification and owner queue.

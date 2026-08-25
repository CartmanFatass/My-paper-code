# C++ batched environment production policy V1

```text
document_kind=engineering_policy_and_fixed_machine_benchmark
scientific_authority=none
production_authority=none
python_reference=test_and_debug_oracle_only
production_fallback=forbidden
```

## Contract

For an object whose frozen production contract is native-only, its experiment
entry point names the exact component from `envs.native.production_backend`,
declares an object-supported positive batch width, calls
`require_cpp_batched_production(...)` before question-relevant activity, and
retains the returned native artifact identity in ordinary preflight evidence.
The guard builds or loads the source/runtime-ABI/build-root keyed C++ module and
fails closed; it never falls back to Python. Existing frozen native-only
contracts remain unchanged.

This engineering guard does not authorize an experiment, create a compute lease,
or change science. Science-card, coordinate, lease, result, and Portfolio gates
remain separate and continue to apply.

Supported native boundaries:

| Component | Production backend | Minimum width | Exact native boundary | Full reset→step C++ |
|---|---:|---:|---|---:|
| `continuous_roster.toy` | `cpp` | 8 | synchronous observation/reward hot path | no |
| `pettingzoo.uav_relay.geometry` | `cpp` | 1 | position integration, A2G/A2A path loss, and access/air/base SINR tensors | no |
| `onlgr.headland90.r03_cal_hold.full_host` | `cpp` | 1 | complete HEADLAND-90 reset-to-terminal C++ kernel over materialized input structs; current Python input adapter is fixture-namespace-only | kernel: yes; panel adapter: not yet |
| `scdmp.uav_sp_order_value.r02.full_host` | `cpp` | 1 | complete tri-UAV sling-corridor 36 m V1 reset-to-terminal C++ kernel over deterministic/materialized inputs; current Python input adapter is fixture-only | kernel: yes; panel adapter: not yet |
| `vnfc.bpcr.r09.full_host` | `cpp` | 1 | complete BPCR r09 C++ host with batched interactive reset, observation-conditioned step and close, plus reset-to-terminal episode execution; separate fixture-only conformance API | yes |
| `risp.g_init_reach.r01.full_host` | `cpp` | 1 | complete G-init r01 C++ host with batched interactive reset, raw-prefix motion/ACK transition and close; Python materializes exact event/action inputs but owns no environment transition or fallback | yes |
| `onlgr.tbvuus.r03.full_host` | `cpp` | 1 | complete four-arm TBVUUS r03 reset-to-terminal C++ host over explicit deterministic tapes; no native RNG, action-word input or Python execution fallback | yes |
| `rcle.tbcfv.r04.full_host` | `cpp` | 1; exact set 1/8/32 | ABI2 RCLE-TBCFV-r04 interactive reset/step/atomic event-apply/terminal/close C++ host; physical transport keys are runtime-only | yes |
| `scdmp.tbcc_order_value.r02.full_host` | `cpp` | 8; exact set 8/12/32/120/144 | ABI2 `QUAD-UAV-PALLET-GANTRY-24P5M-v1` reset/renew/terminal/close C++ host with count plus canonical 13-value native per-renewal reward trace | yes |

Explicitly unsupported production components:

| Component | Reason |
|---|---|
| `pettingzoo.uav_relay.full_environment` | lifecycle, routing, reward, observation, and RNG remain Python-owned; no batched C++ reset→step API exists |
| `semantic_graphon.ridgegate2z.full_environment` | no native environment backend or batched reset→step API exists |

A successful UAV geometry preflight therefore cannot admit a full UAV
environment. A future full-environment experiment must request the
`pettingzoo.uav_relay.full_environment` component and will be refused until that
specific boundary is implemented and registered. RIDGEGATE is refused for the
same reason. This prevents a local native slice from being described as an
end-to-end C++ environment.

The continuous-roster width-one case is also refused for production: the fixed
machine benchmark below found it slower than its Python oracle. Widths 8 and 32
are the current measured efficient region. This is an engineering admission
fact, not a scientific gate.

The ONLGR minimum width of one is derived directly from the authoritative
`run_native_batch` boundary: an empty materialized fixture sequence returns
without loading, while every non-empty sequence passes its exact length to
`headland90_run_batch`. The one canonical exact-stage component string is
`onlgr.headland90.r03_cal_hold.full_host`; no alternate direction-local alias
is admitted. The shared registry calls only
`require_cpp_batched_backend`; it never calls the direction-owned
`production_preflight`. A successful shared guard therefore proves only that
the exact source-keyed full-host C++ kernel exists and loads. The current Python
input adapter still rejects every namespace except the frozen conformance
fixture namespace; the guard does not prove that r03 CAL/HOLD coordinates or a
production panel adapter have been materialized. It grants no CAL/HOLD
coordinates, compute lease, direction activity, panel execution, or production
authority, all of which remain separate Root/CM gates.

The one canonical exact-stage SCDMP component string is
`scdmp.uav_sp_order_value.r02.full_host`; no alternate direction-local alias is
admitted. Its boundary is the frozen task kernel over deterministic/materialized
inputs, with a fixture-only Python input adapter today. The shared registry
calls only `require_cpp_batched_backend`; it never calls a direction-owned
`production_preflight` or other activity-authority check. A successful shared
guard proves only that the source-keyed full-host C++ kernel exists and loads.
It grants no SCDMP identities, empirical activity, compute lease, production,
deployment, or flight authority; those remain separate Root/CM gates.

The one canonical exact-stage VNFC component string is
`vnfc.bpcr.r09.full_host`; no alternate alias is admitted. Its source-keyed
loader calls only candidate `require_cpp_batched_backend(build_root=...)`, which
rejects every non-`None` build-root override, and never calls artifact-identity,
coordinate, activity or production helpers. The native boundary contains both
a deterministic fixture-only conformance API and nonempty batched interactive
reset, observation-conditioned step and close APIs, together with complete
reset-to-terminal episode execution. A successful shared guard proves only
that the ABI-sized native artifact loads. It grants no candidate identity,
coordinate, compute lease, empirical activity, production, deployment or
flight authority; those remain separate Root/CM gates.

The one canonical RISP functional component string is
`risp.g_init_reach.r01.full_host`. Its source/runtime-ABI/build-root keyed
loader calls only candidate `require_cpp_batched_backend(build_root=...)` and
never calls the direction-owned `production_preflight`. The native host owns
the reset, motion/ACK transition and terminal lifecycle for each lane; Python
retains the interactive call loop and materializes exact action/event-prefix
inputs. The registered minimum width of one is an API capability fact only;
the current production grouping is sixteen training lanes and thirty-two
evaluation lanes. Shared admission proves functional implementation and native
artifact identity, not efficiency. It grants no coordinate, direction
activity, compute lease, long-run production, result or Portfolio authority.
The reported single-worker projection remains about 235590 seconds (65.4 CPU
hours), and the RISP CM's result-blind 1/2/4-resource efficiency and equivalence
review remains a separate prerequisite for any production or lease decision.

The one canonical ONLGR TBVUUS component string is
`onlgr.tbvuus.r03.full_host`. Its loader calls only candidate
`require_cpp_batched_backend()` and rejects build-root overrides. It admits the
complete four-arm reset-to-terminal native host over already materialized
deterministic tapes; it does not imply a production namespace adapter, runner,
coordinates, activity or lease. The result-blind fixture efficiency record
`runtime/benchmarks/onlgr_tbvuus_r03_efficiency_20260821.json` reports a 4.230 s
isolated cold build/load, 0.061 s initial warm-cache load, 0.000164 s loader
reuse, B=1/8/32 throughput of 2852.9/2608.4/2552.0 ticks/s, a 770.4 s panel
projection, 48.8 MB peak RSS, 1.863 s compact commit and 0.963 s resume scan.
That review is complete but explicitly withholds lease readiness because no
runner exists. Its isolated-cache DLL SHA-256 is
`653223e0c64683261cd92960bfea4a17f125d6271897cd1c4d996d261a5b3959`,
whereas the current default-cache DLL SHA-256 is
`2e4394929a61ee5f62f2e70370ff5fa5f10ba82650fd6ae8be4becd447f5bc0d`.
Both records share source SHA-256
`86e49d53b6e7cbeb8661c80fc30280be048436153e86384734f07e6c2b4dcbfa`,
build key `0c0651c7bf47c9a1dc21048c30afb57558b5ed2df98fb745f62dc73ecb683072`,
ABI 1, equal ABI sizes and equal file size, but they are not byte-identical;
therefore benchmark timings are not asserted as evidence for identical current
artifact bytes. Functional registration grants no efficiency, production,
coordinate, activity, result, compute-lease or Portfolio authority.

The one canonical RCLE TBCFV component string is
`rcle.tbcfv.r04.full_host`; it is distinct from `continuous_roster.toy` and
has no alias. The source/MSVC-toolchain/runtime-ABI/flags/interface/magic and
resolved-build-root keyed loader calls only candidate
`require_cpp_batched_backend(build_root=...)`. Its exact validated width set is
1, 8 and 32, so other positive widths fail before native loading. The accepted
boundary is ABI 2, magic `0x52434c4554424347`, with FixtureInput/StepInput/
EventInput/Snapshot sizes 224/64/64/464. Source, build and current artifact
SHA-256 values are respectively
`ddb14c33d822924b21b872713745f242fee92f16b4329efed439a1e2b816a910`,
`8e80ba3cf3ba026c486d75d330aa9a99f820fe60803334dce7841032a48a5f91`,
and `023eecbc0a69710ee6a4fe06aa8e1b0b5165870bbcfc5a7ae2198e86372baf15`
(156160 bytes). The stale ABI 1 magic `0x52434c4554424346` and artifact
`69563e66d594f1ed40a249d7433699fd9529236c76e8eaa799a3f57517799790`
are explicitly not accepted.

At tick 24 the pre-event snapshot is lifecycle metadata and cannot be exposed
as an actor observation. The ABI2 `apply_event` call validates and installs all
lanes atomically before the post-event observation; ACTIVE_CONTINUATION remains
distinct from and ordered before NEW_EPOCH in the supplied batch. Physical
transport keys preserve survivor/newcomer identity through sorting, crossing
and churn, but are runtime row-linkage only and are excluded from the public
observation and model tensors. Python only marshals candidate fixture structs
and has no environment transition or oracle fallback. Shared registration
proves implementation and artifact identity only. It grants no science,
identity, coordinates, activity, production, result, compute lease or Portfolio
authority.

The one canonical SCDMP TBCC component string is
`scdmp.tbcc_order_value.r02.full_host`. Its loader calls only candidate
`require_cpp_batched_backend(build_root=...)`; because that candidate owns one
fixed source-keyed build root, every non-`None` override fails closed. Shared
production widths are exactly 8, 12, 32, 120 and 144. Candidate width 1 remains
conformance-only, so shared B=1 and B=2 are rejected before native loading. The
accepted `QUAD-UAV-PALLET-GANTRY-24P5M-v1` boundary is ABI 2, magic decimal
6071489204069610049, source SHA-256
`ea2149b187ba65c9229f0ada9c3bd55bd0f424ec5a5830de1f454585b488de38`,
build key `9a9801e94e1b02468df1e3d59e0c0055b85e2d02306c018bb275b69e0f718fe3`,
and current DLL SHA-256
`df1097603c3fd2e1f66875e5d3209fcc509609f870569a205efc83c607a7bb9d`
(177664 bytes). Reset/Renewal/HostOutput/SetupInput/SetupOutput/PrimitiveInput
sizes are 64/320/336/24/24/160. ABI 1, old source
`6cbdd16c493cd6f0904e44421a087767bb7a79e7f39bfd8b3c13f9221731bf26`,
old build `5669a6193a3799fef4ea0db48d2e23205ca85e8eeb8ef8b43bb29c2e0c548882`,
old artifact `30f4a848054f748f76944581c042b4b5de41926628c9e00d1df1f6746f5049f3`,
and old HostOutput size 224 are stale and rejected.

Each ABI2 HostOutput carries `last_hold_reward_count` and a canonical 13-value
native reward trace. The count must equal `ticks_advanced`; the active prefix
must be finite and the inactive tail must be zero. Duration-correct PPO consumes
these native per-tick rewards only; Python reward reconstruction and fallback
are forbidden. The unchanged result-blind benchmark
`runtime/benchmarks/scdmp_tbcc_r02_efficiency_20260821.json`, verified at file
SHA-256 `cde0847e02fb80dc96986921005d20712f120d496f5bb0105aab18a3eb3669eb`,
is historical ABI1/source-6cbdd/build-5669/artifact-30f4/HostOutput-224 evidence
only. It is not current ABI2 performance evidence, does not reaccept the
benchmark, and grants no lease readiness. This registration grants no empirical
identity, coordinate, model, checkpoint, training, evaluation, result,
activity, production, compute lease or Portfolio authority.

## P0 compute-time rule

Stopping or abandoning an authorized computation because a toy environment
exhausted wall time is a P0 engineering incident. It is never evidence of
scientific failure, nonidentification, direction pause, or Portfolio disposition.
The owning CM must preserve a blinded atomic/resumable frontier, identify the
backend/batching/loader/profile defect, repair it without changing science, and
resume under the ordinary lease. A new run root is used when the launcher
contract requires one; coordinates, seeds, thresholds, treatments, RNG order,
and result meaning do not change by implication.

## Mandatory end-to-end efficiency review

Source completion is not sufficient for a long-experiment lease. Before any
new long empirical run, the owning CM must review the entire execution chain
and return a measured, result-blind efficiency packet to Operational Root. The
review covers, at minimum:

1. reset/step/terminal environment work and native adapter boundaries;
2. native loader/build-identity caching (cold preflight versus warm calls);
3. batch formation, policy forward pass, recurrent-state handling and
   backward/optimizer updates;
4. rollout collection, episode packing and worker/CPU-thread utilization;
5. evaluation/control consumers and aggregation/inference preparation; and
6. serialization, checkpoint/receipt writes, atomic publication and resume
   scanning.

For each material stage, CM records reproducible baseline and optimized
measurements: supported batch widths, concurrency, steady throughput,
process-cold cost, CPU utilization, peak RSS, durable/scratch I/O and projected
full-panel wall time. CM selects the object-supported sweep and explains its
coverage; no universal `1/8/32` matrix or fixed concurrency combination is
implied. A native optimization is admitted only when Python/reference outputs,
lifecycle identities, RNG/order, artifact hashes and complete-panel counts
remain equal under the declared tolerance. Python remains a test/debug oracle
and there is no silent fallback in a frozen native-only contract.

The review must identify the dominant bottleneck and apply
semantics-preserving optimizations where available (batching/vectorization,
process-local loader cache, fused native kernels, bounded worker parallelism,
chunked I/O and resume-friendly checkpoint batching). It must not drop rows,
sample away registered work, shorten the horizon, alter treatment/comparator
semantics or introduce an unregistered approximation. If a toy or UAV chain
projects to days merely because this review was skipped or an obvious
batching/backend defect remains, this is a P0 engineering finding: withhold
the heavy lease, preserve the blinded frontier, repair and remeasure rather
than treating runtime as scientific evidence.

The CM packet must include:

```text
efficiency_review=COMPLETE|REPAIR_REQUIRED
chain_coverage=environment|loader|batch|forward_backward|rollout|evaluation|io|resume
baseline_measurements=<exact commands and outputs>
optimized_measurements=<exact commands and outputs>
dominant_bottleneck=<plain causal statement>
semantic_equivalence=<oracle/hash/RNG/order/lifecycle evidence>
projected_full_panel_cost=<CPU/wall/RSS/storage>
rollback_nodes=<backend|batch width|cache|worker/chunk|I/O choices>
lease_readiness=<READY|WITHHOLD>
```

This is an engineering admission gate only. It does not authorize science,
coordinates, identities, a lease, production or deployment, and it does not
transfer Portfolio or EM authority.

## Pre-build native-first gate

The efficiency review is preceded by a build-order rule. A new or materially
revised native-only experiment freezes its native C++ batch boundary,
source-keyed loader/ABI contract, object-supported batch-width and concurrency
model, and a reference benchmark before a production runner is written. The
native host and benchmark harness are constructed first; a serial Python
production chain is not an acceptable scaffold to port later.

Python may be present only as a clearly isolated reference oracle, TEST fixture,
metadata/lifecycle adapter explicitly allowed by the native boundary, or test
helper. Any production entry point for a frozen native-only object that contains
scalar Python environment or rollout loops, implicit `python_reference`, or an
unspecified batch/worker contract is `REPAIR_REQUIRED` before coordinates,
identities, models, leases or question-relevant activity exist. Missing native
support is CM construction work and may withhold only the affected lease; it is
never science, portfolio, or direction-stop evidence.

The native-first gate does not require parallel execution where it would change
RNG/order, pairing, checkpoint or artifact semantics. In that case CM must
return the exact reason and a bounded native batch plan before any production
source is admitted. Once equivalence is proven, bounded workers and widths are
the default optimization path.

## Loader incident and repair

The first 2026-08-20 benchmark exposed a P0 loader defect. Every environment
step or episode re-entered Windows toolchain discovery and recomputed the native
identity even though the source-keyed extension was already loaded. That made a
microsecond native call appear to cost milliseconds and made a complete
continuous-roster episode appear to cost about 2.4 seconds.

Both native loaders now use a process-local cache keyed by source bytes,
runtime ABI, compiler flags, interface version, and resolved build root. A warm
call returns the already loaded module before compiler/toolchain probing. Source
byte or build-root changes produce a new key and load; the underlying extension
loader still includes compiler identity and source digest in its artifact name.
The process-cold preflight remains explicit and fail-closed.

## Fixed-machine evidence — 2026-08-20

Machine: Windows 10 build 26200, AMD64 Family 25 Model 117, Python 3.10.20,
NumPy 1.26.3, PyTorch 2.7.0+cpu. All runs were nonformal, CPU-only, single
PyTorch thread, alternating order, exact-oracle gated, and used no training or
scientific result data.

### Continuous-roster complete 48-step episodes

Command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m tools.benchmarks.benchmark_continuous_roster_toy_cpp_backend --batch-sizes 1 8 32 --capacity 8 --repeats 7
```

Process-cold native preflight: `3.155192 s`. Steady medians exclude that
one-time cost.

| Batch | Python median | C++ hot-path median | Speedup | Exact outcome |
|---:|---:|---:|---:|---:|
| 1 | 0.003160 s | 0.003814 s | 0.829x | yes |
| 8 | 0.023238 s | 0.006253 s | 3.716x | yes |
| 32 | 0.095402 s | 0.015312 s | 6.231x | yes |

The benchmark covers construction/reset through terminal outcome, while
truthfully labeling only observation/reward as native.

### UAV native geometry, batch 1/8/32

Command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m tools.benchmarks.benchmark_uav_cpp_backend --scope geometry_kernel --batch-sizes 1 8 32 --repeats 11 --iterations 3 --output <runtime-json>
```

Process-cold native preflight: `3.607166 s`. Warm calls were bitwise equal.

| Batch | Python median/call | C++ median/call | Speedup |
|---:|---:|---:|---:|
| 1 | 0.003295 s | 0.000424 s | 7.765x |
| 8 | 0.025664 s | 0.000537 s | 47.759x |
| 32 | 0.104392 s | 0.001005 s | 103.887x |

### UAV complete environment step

The existing full-environment oracle harness ran 31 alternating samples per
consumer. Although only geometry is native, complete transition, internal state,
and RNG were exact, and the cached native geometry improved all three complete
Python-owned environment consumers:

| Consumer | Python median/step | C++-geometry median/step | Speedup |
|---|---:|---:|---:|
| routed | 0.034982 s | 0.032391 s | 1.080x |
| energy | 0.038586 s | 0.036003 s | 1.072x |
| forced | 0.085140 s | 0.083592 s | 1.019x |

These timings justify the UAV **geometry** default changing from
`python_reference` to `cpp`. They do not claim a full C++ UAV environment and do
not authorize UAV production.

## Rollback nodes

1. Change the three UAV geometry default constants back to
   `python_reference`; explicit C++ and oracle tests remain available.
2. Disable a component by setting only its registry declaration to unsupported;
   callers then fail closed before activity.
3. Revert the process-local fast cache while retaining the source-keyed extension
   cache if a cache-identity defect is found; this restores slow but safe loads.
4. Revert the shared registry/guard only together with every future entry-point
   consumer. Never leave a production entry point with an implicit Python
   fallback.

No active RISP/SCDMP run, science card, coordinate, result artifact, lease,
Portfolio decision, provider session, or UAV production authorization was
modified by this package.

## Phase 2: fused deterministic radio tensors

The authoritative relay step was separated before expanding the native seam:

| Step responsibility | Owner after Phase 2 |
|---|---|
| user movement and every RNG draw | Python |
| energy failure/charging/return lifecycle | Python |
| action validation, safety guard and discrete/continuous action law | Python |
| position integration and clipping | batched C++ numeric slice |
| A2G/A2A/base path loss | batched C++ numeric slice |
| access, directed air, UAV→base and base→UAV SINR tensors | batched C++ numeric slice |
| hard/soft connection objects and handover counters | Python |
| routing paths, widest-path objects and packet queues | Python |
| reward, observation, state, info and artifact semantics | Python |

The radio kernel consumes only already-materialized contiguous positions and
path-loss tensors plus explicit scalar configuration. It creates no RNG, owns no
mutable environment state and writes no artifact. Routed/energy preserve their
receiver-exclusion interference law; forced preserves its distinct law. FDMA and
non-FDMA reductions, finite-radius inclusion, zero-interference/noise-only
branches, output shapes, finite values and both receiver-exclusion modes have
independent Python-oracle tests.

Real routed, energy and forced consumers use the fused tensors for authoritative
channel updates and repeated observation/routing lookups. Cache validation is
performed once around a known non-mutating observation or routing region;
external direct state mutation is still checked before entering that region.

### Phase-2 radio-kernel benchmark

Command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m tools.benchmarks.benchmark_uav_cpp_backend --scope radio_kernel --batch-sizes 1 8 32 --repeats 7 --iterations 2 --output <runtime-json>
```

Every tensor was bitwise equal. Medians:

| Consumer interference law | B=1 | B=8 | B=32 |
|---|---:|---:|---:|
| routed/energy | 26.017x | 71.734x | 92.069x |
| forced | 17.460x | 69.897x | 98.940x |

### Phase-2 complete consumer step

The 31-sample alternating full-transition benchmark retained exact public
payload, internal state and RNG:

| Consumer | Python median | C++ numeric median | Speedup |
|---|---:|---:|---:|
| routed | 0.021568 s | 0.008942 s | 2.412x |
| energy | 0.029055 s | 0.017105 s | 1.699x |
| forced | 0.021342 s | 0.008660 s | 2.464x |

The reset→step width matrix separately measured 1, 8 and 32 real environment
instances. Environment instances are still sequenced in Python, and each
consumer currently invokes the native numeric kernel at width one; the matrix
therefore measures aggregate real-consumer throughput without claiming a fused
full-environment batch:

| Consumer | B=1 | B=8 | B=32 |
|---|---:|---:|---:|
| routed | 2.550x | 2.189x | 2.471x |
| energy | 2.159x | 1.724x | 1.823x |
| forced | 3.018x | 2.581x | 2.745x |

Process-cold preflight was `3.712426 s` and is excluded from steady timings.
All nine batch cells matched reset payload, step payload, named internal state
and RNG exactly.

### Remaining unsupported surface and measured bottleneck

`pettingzoo.uav_relay.full_environment` remains fail-closed unsupported. There
is no cross-environment batched reset→step API: Python still sequences RNG,
lifecycle, routing/queue mutation, reward and observation. A geometry/radio
preflight cannot satisfy that full-environment component.

Post-implementation one-step profiles identify the next residuals rather than
another safe automatic promotion:

- routed: observation/local-view construction and exact communication-cache
  identity validation;
- energy: widest-path routing, repeated link-capacity lookups and graph/reward
  materialization;
- forced: observation/local-view construction and retained-radio identity
  validation.

Those objects contain Python lifecycle and structured routing/observation
semantics. Moving them requires a separately proven phased vector-environment
interface, not a larger claim for the current stateless numeric kernel.
`semantic_graphon.ridgegate2z.full_environment` likewise remains unsupported:
it still has no native batch API, so SGSP admission does not change.

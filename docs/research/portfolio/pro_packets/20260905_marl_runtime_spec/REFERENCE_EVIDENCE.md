# Source evidence used by the runtime engineering draft

Root synthesis of six independent Luna/max static source studies. This packet contains
source-backed engineering observations, not benchmark results. No dependency installation,
training or library benchmark was performed. The source commits, origins, licenses and local
navigation inventories are in SOURCE_MANIFEST.json; detailed evidence is under worker-reports.
Primary upstream links in those reports are fixed to the inspected commits. They preserve
the distinction between local code observed, external dependency behavior not inspected,
and performance consequences that remain unmeasured.

## Implementations and what they actually demonstrate

| Reference | Core source and observed mechanism | Draft consequence and limit |
| --- | --- | --- |
| EPyMARL | `src/runners/parallel_runner.py:19–47,127–195` creates one environment process/Pipe and a synchronous per-step receive barrier; `basic_controller.py:26–40,63–78` batches shared agents as B×A; `episode_buffer.py:30–113` allocates B×T×A storage and converts Python arrays at update. | Name the actual environment/agent/time axes, IPC and transfer boundary. A parallel runner is not proof that learner time or inactive environments are efficiently batched. No blanket mandate to copy its process topology. |
| MAPPO on-policy | Shared runners flatten R×A for one policy call per timestep; separated runners loop over agents and retain separate policies/buffers. `onpolicy/envs/env_wrappers.py` sends all actions then receives/stacks responses synchronously. NumPy buffers move through Torch/device conversion and back during collection. | Preserve policy-sharing meaning, rollout/update frequency, sequence masks and chunk tail treatment. Treat transfers, barriers and redundant full-rollout logprob calculations as hypotheses, not measured savings or permission to delete scientific output. |
| BenchMARL | `benchmarl/experiment/experiment.py:447–567` distinguishes native batch environments from SerialEnv/ParallelEnv and uses SyncDataCollector; later collection/training handles TensorDict groups and sampling/train/buffer devices. VMAS vectorization differs from PettingZoo's parallel-agent API. | Define the layer and shape of parallelism. The exact TorchRL worker/kernel behavior is outside this inspected clone. Compile settings and external native kernels do not establish an end-to-end speedup. |
| JaxMARL | IPPO/VDN use environment/agent/seed vmap and time/update/GAE scan with outer jit. `jaxmarl/environments/smax/smax_env.py:340–411` includes eight inner world steps by default; `speed.py:196–203` compiles before blocked steady-state timing. | Count nested simulator work and distinguish compile-inclusive invocation cost from steady state. Vectorization is not time independence or multi-device sharding; source selection and RNG split order are part of the computation. |
| Mava | `mava/systems/ppo/anakin/ff_ippo.py:270–370` uses device pmap, update-batch vmap and temporal scan with device/batch gradient reductions. Sebulba uses CPU vector environments, device transfers, bounded queue backpressure and a sharded learner. | State the actual architecture rather than use an old project description. Sample-to-insert ratio, policy staleness, queueing, terminal observations and truncation bootstrap are scientific/algorithmic behavior, not removable overhead. Do not import its service machinery into a single-use HMASD object. |
| MARLlib | Own wrappers construct per-agent dictionary payloads; policy mappings differ from joint-Q grouping. Centralized critic and Q postprocessing align/copy/pad/stack agent batches. Bundled Ray patches apply only if installed by its patch script. | Distinguish inspected wrapper/postprocessing from old external RLlib scheduler/object-store behavior. Default resource fields are requests, not observed process topology. The study proposes possible measurements; new serialization/object-store telemetry is not adopted by this spec. |

Detailed source paths, lines, short excerpts and fixed-SHA links are in:

- `worker-reports/epymarl/CORE_EVIDENCE.md`
- `worker-reports/on-policy/CORE_EVIDENCE.md`
- `worker-reports/BenchMARL/CORE_EVIDENCE.md`
- `worker-reports/JaxMARL/CORE_EVIDENCE.md`
- `worker-reports/Mava/CORE_EVIDENCE.md`
- `worker-reports/MARLlib/CORE_EVIDENCE.md`

Root used the compact returned core-call-chain analyses, rather than ingesting full library
trees. These reports do not establish that every line of any external dependency was read.
They provide implementation examples for the review; the Pro source-access contract remains
the listed HMASD artifacts at its fixed evidence commit, not automatic access to linked repos.

## Mapping evidence to the proposed requirements

1. **Full operation counts:** MAPPO's rollout axes, JaxMARL's nested world steps, Mava's
   device/update/env dimensions and VNFC's comparator multiplication all show why a scalar
   environment-step count alone can miss dominant work. Count mandatory learning, replay,
   evaluation, independent checks and publication at the original scientific support.
2. **Explicit batching and state ownership:** shared-policy flattening and JAX transformations
   provide concrete alternatives to scalar calls. They also expose recurrent state, masks,
   terminal/bootstrap and RNG dependencies that prevent arbitrary loop removal.
3. **Honest parallel and device boundaries:** Pipes and sync collectors, VMAS native batching,
   JAX device transformations, CPU/GPU buffer paths and Sebulba queues are distinct mechanisms.
   Inspect the actual path and scope before claiming a useful parallel speedup.
4. **Complete timing:** JaxMARL's explicit compile/blocking distinction and Mava's blocked
   learner/evaluation clocks justify declaring synchronization and cold/steady-state scope.
   Include the real final artifact path; a fast model kernel is insufficient.
5. **Minimal engineering scope:** library-wide registries, distributed workers, queue systems,
   patch installers and logging backends are context for tradeoffs, not a proposal to reproduce
   them. Prefer an existing batched path and one bounded native computation where appropriate.
6. **Thresholds remain policy:** no inspected library supplies a matched proof that HMASD toy
   jobs should take 45 minutes or UAV jobs 12 hours. Those are the owner's chosen investigation
   triggers. Pro must define their unit and their relationship to existing tighter caps.

## HMASD-specific contrary evidence and applicability

Existing EFFICIENCY_PRACTICES records a historical small-tensor CPU advantage and limited
multi-process GPU scaling on a particular WDDM setup. They are conditional measurements;
the current remote Linux/CUDA route is different. ENGINEERING_ADDITIONS contains useful
batch/reconstruction cautions but also categorical statements derived from that older setup.
The new spec should preserve the observations and narrow the categorical guidance to those
conditions, avoiding a fresh unrequested CPU/GPU or worker-count benchmark for every object.

N3's complete original A05 now finishes its formal process in 2.40 seconds, with actual
batch/native calls and full original measurements. Its 25.5-second figure was a prospective
allowance, not a slow measurement. It does not need forced additional acceleration or timing.
CBSC reached publication and subsequently failed before the required fifteen tables/summary
completed; passing a fast partial test is not full-path acceptance. Its failure interpretation
belongs to its separate reproduction/intake, not to this library study.

VNFC is the actual over-cap case: optimized-language presence plus a coarse call did not
eliminate serial full-comparator work. Its new exact structural simplification and batch
candidate come from the accepted direction Pro decision, not a claim that PPO/JAX libraries
solve its exact arithmetic or checker independence. All proposed new costs remain unknown.

## Navigation integrity and limitations

Local AGENTS files are navigation overlays on pinned upstream sources. Each points to real
entrypoints and applicable modules; the index and backup make them recoverable from HMASD.
Existing upstream files must be preserved, and module facts are revisited at a new commit
rather than silently carried forward. No source license is replaced by the local overlay.

During MARLlib navigation generation, one relative-path tool call mistakenly wrote overlays
under HMASD. Root preserved those bytes in local scratch, restored the two previously clean
tracked authority files from the current commit, and moved only the identified misplaced
new overlays out of the project tree. No scientific source/history/evidence was deleted.
The worker resumed with absolute paths. This correction is a scope-handling error, not an
observation about MARLlib performance; the final manifest must report only correct locations.

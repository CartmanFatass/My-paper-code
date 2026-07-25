# UAV C++ batched environment backend

Date: 2026-07-25

```text
status=PM_ACCEPTED_ISOLATED_NATIVE_SLICE
implementation_state=COMPILED_BITWISE_ORACLE_AND_SPEED_GATE_PASS
owner=project_manager
purpose=accelerate_reused_uav_environment_without_changing_science
active_formal_run_backend=python_frozen_source_unchanged
target_backend=cpp_cpu_batched_stateless_kernel
python_rng_owner=true
python_lifecycle_owner=true
python_evidence_owner=true
compatibility_layer=forbidden
active_environment_integration=false
semantic_oracle_scope=first_native_kernel_boundary
```

## Decision

The reusable UAV environment should move its deterministic hot path to C++,
but it should not be translated class-by-class. The performance target is one
native call for a whole batch of environments and one physical step. This
removes Python scalar loops and per-row process/Pipe traffic together; porting
small helpers while retaining the same call count would not achieve the
requested best-speed boundary.

The completed formal charge-rotation G2 run remains bound to source commit
`8350263ef73b15f10b6d2bcac2583687aad7cade` and the existing Python backend.
The native slice was compiled only after that process was terminal. It cannot
relabel, resume with, or modify the formal evidence.

## Ownership boundary

Python remains the sole owner of:

- reset and the frozen NumPy RNG namespaces, draw order and per-step channel
  randomness;
- immutable energy/profile ledgers and episode identity;
- ACTIVE/CHARGE_ABSENT/TERMINAL lifecycle state and ordered events;
- source controllers, source facts, reward and observation assembly;
- policy, recurrence, replay, PPO, checkpoints, metrics, bootstrap, artifact
  authority and registered result selection.

C++ is a pure deterministic transform. It owns no persistent environment state,
RNG, worker, file, cache authority or lifecycle event. Its target accepted
surface is a fused batch kernel over already-materialized inputs:

```text
step_physics_communication_batch(
    uav_positions: float64[B,8,3],
    user_positions: float64[B,30,3],
    ground_bs_positions: float64[B,G,3],
    guarded_velocities: float32[B,8,3],
    active_or_unavailable_masks: bool[B,8],
    channel_draws_and_config: explicit contiguous arrays/scalars
) -> {
    next_uav_positions: float64[B,8,3],
    directional_path_loss: explicit float64 matrices,
    sinr_and_capacity: explicit float64 matrices,
    connection_masks: explicit bool/int matrices
}
```

No output is committed to the Python environment until the whole call returns
and its shapes/dtypes are validated. The kernel preserves the existing scalar
iteration and reduction order before any native parallel reduction is allowed.
It has no implicit global cache; input identity and invalidation remain visible
to Python.

Routing-path object construction, packet-flow causality, queue/charge
transitions and reward/observation assembly remain Python in the first slice.
They move only if profiling after the accepted first slice shows that they are
the new material bottleneck and a separate exact oracle can cover them.

## Toolchain and loading

The active CPU environment contains Python 3.10.20 and PyTorch 2.7.0+cpu. The
accepted toolchain is Visual Studio Build Tools 17.14.37, MSVC 14.44.35207 and
Ninja 1.12.1. The CPU-only PyTorch extension loads from an explicit ignored
cache outside tracked sources. Its short directory key is a digest of the full
Python, torch, compiler, CPU, flags and native-source identity. Compiled
binaries are never committed or reused across an identity change.

The focused suite compiled and imported the first CPU op with the registered
interpreter and `torch_threads=1`; all 10 tests passed. It covers exact
shape/dtype/value behavior, non-binary float32 movement and clipping order,
inactive-action mutation, fail-closed payload validation, and reuse of the same
compiled module from a second Python process. Unicode repository paths are kept
out of Ninja files by copying the content-identified native source into the
ASCII build cache before compilation.

The first implemented input is the already-prepared, backhaul-guarded velocity
`float32[B,U,3]`, after Python has applied lifecycle, failure, limp-home,
docking, charge and backhaul-guard decisions with the existing float32 action
rounding. This makes the ownership boundary executable: the fourth policy/dock
coordinate and every lifecycle/topology decision stay in Python, while one C++
call updates the whole batch and generates UAV-user, UAV-UAV and UAV-base
path-loss matrices from the resulting positions.

## Proof-sized semantic oracle

Run the Python reference and native candidate from the same reset seed/profile
and the same dense action trace. At every step compare:

- positions, batteries, station occupancy/queues, lifecycle states and ordered
  events;
- active/executed/physical masks and inactive/terminal action behavior;
- path loss, SINR, capacities, connections, routing inputs and QoS;
- observations, critic state, reward, safety score, return cost and source
  facts; and
- every Python RNG state and draw count.

Integer, mask, event and RNG evidence is exact. Float evidence targets bitwise
equality by preserving dtype and reduction order. A numeric tolerance is not a
default escape hatch; any unavoidable difference requires a separate protected
scientific decision before the native backend can become active.

The accepted first-slice oracle is deliberately limited to the native ownership
boundary: batched position updates, movement boundaries, inactive-action
mutation, three directional path-loss matrices, input/output layout and cache
identity. Lifecycle, charge, queue, reward, observation and RNG remain Python
owners and therefore cannot be claimed by this isolated kernel test. A later
active-environment integration must compare those full transition surfaces
before it may replace the Python path.

## Performance acceptance

Only after semantic closure, run alternating warmed Python/native trials on the
registered AMD CPU with one native thread. Report exact workload, batch size,
repeats, median time, call count and transition/RNG equality. The first
cross-file native slice is retained only when median speedup is at least 20%.
If it misses, increase fusion at the same pure boundary or remove the native
slice; do not keep a compatibility backend with negligible value.

The final target is to replace `PersistentG2VectorEnv` process/Pipe stepping
with one batched native call while keeping the public G2 transition ABI. The
The superseded Python implementation is removed only after active-environment
integration passes its full transition oracle; Git history is the archive.

The retained benchmark artifact is
`logs/nonformal_uav_cpp_backend_benchmark_20260725_pm1/result.json`. With
`B=8`, eight UAVs, 30 users, two bases, seven alternating repeats and five calls
per repeat, the Python scalar median is `0.04657848 s`, the C++ median is
`0.00070086 s`, and the single-thread speedup is `66.459x`. All benchmark
outputs are bitwise equal and the frozen `1.20x` retention threshold passes.

## Ordered realization

1. Completed: finish the Python formal run without source changes.
2. Completed: provision MSVC/Ninja and pass build/import/cache proof.
3. Completed: implement batched movement and directional path loss in new
   native/loader/test paths.
4. Completed: pass the kernel Python oracle and mutation negatives.
5. Completed: pass the frozen performance-retention threshold.
6. Pending: expand fusion only from measured residual hotspots, then replace and delete
   the superseded Python active line in one accepted Git boundary.

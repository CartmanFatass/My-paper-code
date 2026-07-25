# UAV C++ batched environment backend

Date: 2026-07-25

```text
status=FROZEN_ENGINEERING_BOUNDARY
owner=project_manager
purpose=accelerate_reused_uav_environment_without_changing_science
active_formal_run_backend=python_frozen_source_unchanged
target_backend=cpp_cpu_batched_stateless_kernel
python_rng_owner=true
python_lifecycle_owner=true
python_evidence_owner=true
compatibility_layer=forbidden
```

## Decision

The reusable UAV environment should move its deterministic hot path to C++,
but it should not be translated class-by-class. The performance target is one
native call for a whole batch of environments and one physical step. This
removes Python scalar loops and per-row process/Pipe traffic together; porting
small helpers while retaining the same call count would not achieve the
requested best-speed boundary.

The in-flight formal charge-rotation G2 run remains bound to source commit
`8350263ef73b15f10b6d2bcac2583687aad7cade` and the existing Python backend.
Native work is isolated in new paths until its oracle and benchmark pass. It
cannot relabel, resume with, or modify that formal evidence.

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
RNG, worker, file, cache authority or lifecycle event. Its first accepted
surface is a fused batch kernel over already-materialized inputs:

```text
step_physics_communication_batch(
    uav_positions: float64[B,8,3],
    user_positions: float64[B,30,3],
    ground_bs_positions: float64[B,G,3],
    actions: float32[B,8,4],
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

The active CPU environment contains Python 3.10.20 and PyTorch 2.7.0+cpu with
`torch.utils.cpp_extension`, but currently has no C++ compiler, CMake, Ninja or
standalone pybind11 installation. The smallest maintained route is a CPU-only
PyTorch C++ extension built with MSVC and loaded from an explicit ignored cache
outside tracked sources. Compiled binaries are never committed or reused across
Python, torch, compiler or CPU-ABI changes.

Before environment code is written, the toolchain proof must compile and import
one tiny CPU op with the registered interpreter, `torch_threads=1`, verify exact
dtype/shape/value behavior, and verify a second import reuses the explicit
build cache. A compiler install is delayed until the in-flight formal process is
terminal so installer CPU, disk activity or restart behavior cannot interfere
with that evidence.

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

The oracle includes steady flight, movement boundaries, LEAVE, queue
contention, CHARGE, REJOIN, terminal/depletion, inactive-action mutation,
position/config/mask invalidation and trial-position non-persistence.

## Performance acceptance

Only after semantic closure, run alternating warmed Python/native trials on the
registered AMD CPU with one native thread. Report exact workload, batch size,
repeats, median time, call count and transition/RNG equality. The first
cross-file native slice is retained only when median speedup is at least 20%.
If it misses, increase fusion at the same pure boundary or remove the native
slice; do not keep a compatibility backend with negligible value.

The final target is to replace `PersistentG2VectorEnv` process/Pipe stepping
with one batched native call while keeping the public G2 transition ABI. The
Python implementation is removed after native acceptance; Git history is the
archive.

## Ordered realization

1. Finish the in-flight Python formal run without source changes.
2. Provision MSVC/Ninja and pass the tiny extension build/import/cache proof.
3. Implement fused batched movement and directional communication in new
   native/loader/test paths.
4. Pass the stepwise Python oracle and mutation negatives.
5. Benchmark; retain only at the frozen speed threshold.
6. Expand fusion only from measured residual hotspots, then replace and delete
   the superseded Python active line in one accepted Git boundary.

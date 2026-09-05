# MARL runtime engineering specification — draft

Status: DRAFT_NOT_OPERATIVE. Root-authored under the owner's 2026-09-05 instruction;
the six-library source evidence is being assembled. A complete proper-node Pro decision
must settle the proposed provisions and the VNFC appendix before activation. This draft
does not itself approve source, change a frozen object, or authorize a measurement.

## Purpose and boundary

Make a complete scientifically defined MARL observation affordable through appropriate
algorithms, data layout and execution. Diagnose expensive implementations before treating
their runtime projection as a property of the research question. Keep required comparisons,
worlds, seeds, observations, endpoints, independent checks and result branches intact.

Apply this guidance to CM, implementers and reviewers. Use the existing science card,
engineering assignment, cost line and intake rather than adding services, registries,
validators, profiling infrastructure, a separate approval process or another launch gate.
The existing four launch conditions and code/testing budgets remain the baseline. A fixed
card's tighter cap, numerical constraints or execution topology takes precedence until the
proper node explicitly changes that engineering restriction.

## When the runtime warrants investigation

Proposed interpretation for review: a complete prospective arm/seed invocation exceeding
45 minutes on a toy host or 12 hours on a UAV host triggers a concrete engineering review.
Declare the host category in the existing assignment; do not infer it from a filename or
rename a host to obtain the larger threshold. Include required rollout, learning, replay,
evaluation, checks and publication in the invocation, not training time alone. Report the
whole study's elapsed critical path and aggregate work as well, so many individually small
arms cannot hide an unreasonable total investment.

These are investigation thresholds, not scientific outcome rules or new grants of compute.
Do not launch an arm whose existing projection exceeds its actual cap. Review source and
existing evidence first; a new timing or equivalence experiment needs a bounded assignment
under the applicable authority. Existing valid results are not invalidated retrospectively.
Pro must explicitly settle whether these thresholds use this per-invocation interpretation
or a different study-level unit, and make the final text unambiguous.

## Identify algorithmic work before choosing an accelerator

CM traces one complete call chain from input through environment/rollout, policy, learner,
comparison/evaluation and publication. Record the few dominant terms and their exact counts:
environment steps, environments/replicas, agents, horizon, update epochs/minibatches,
branches/candidates, comparator calls, independent verification and output work as applicable.
Account for nested products; a cheap physical tick can coexist with an expensive comparator.
Distinguish scientific support that must be enumerated from an inefficient implementation
of the same estimator. Exact algebraic reuse/decomposition needs an explicit equivalence
argument and focused verification under the object's actual numerical contract.

Use measured full-stage or full-batch costs with their source SHA, host, device, dimensions,
thread count and timed scope. A synthetic unit-time extrapolation is a planning estimate,
not a measured complete runtime or optimized lower bound. State uncertainty and uncovered
work. Never set unknown terms to zero or divide an old serial time by a core count.

## Batch independent dimensions and keep causal dimensions ordered

Prefer the existing verified tensor path for independent environment, agent, replica or
counterfactual dimensions. State their shapes and state ownership. Shared policy inference
can flatten compatible environment/agent axes; separate policies, masks and recurrent state
must retain their semantics. Time steps, autoregressive actions and recurrent dependence
stay ordered unless a valid algorithm specifically removes the dependence.

Allocate rollout/replay storage once at the needed shape where practical; avoid per-agent
tensor construction, per-step host/device round trips, scalar GPU synchronizations and
repeated packing of unchanged data in a demonstrated hotspot. Preserve batch boundaries,
masking, terminal versus truncation behavior, recurrent reset, bootstrap and sampling law.
Changing rollout width can change sample order, update frequency, RNG or reduction order;
it is not automatically a behavior-preserving performance edit.

## Choose native, compiled and parallel execution by the actual hotspot

For a CPU-bound Python hotspot, first use appropriate array/tensor batching or a coarse
native/compiled boundary over substantial work. C++ code and compiler optimization flags
alone do not establish efficient execution: inspect serial loops, allocations, repeated
construction and call granularity inside the native path. Do not add a language boundary
for work that is not the bottleneck. GPU/JIT/compilation presence is likewise not a speedup.

For native independent work, a fixed team with bounded private mutable state and stable
logical output order can be appropriate. Use the actual execution node's available CPU,
memory and accelerator constraints. Account for nested BLAS/OpenMP/Torch threads and
oversubscription; avoid duplicated GPU contexts merely to parallelize small kernels.
Shared immutable inputs may be reused only through their genuine dependencies. Independent
scientific checkers must remain independent rather than reusing the producer's answer.

Proposed scope clarification for review: in-process tensor batching and a bounded fixed
native team for a named dominant computation are ordinary performance implementation when
explicitly described in its engineering assignment. They do not authorize distributed,
multi-process or multi-node frameworks, general worker pools, schedulers, retries, leases
or new runtime guards. The final Pro text must reconcile any overlap with Engineering
Scope §4 and with pre-existing single-thread cards rather than silently overriding them.

## Measure complete work with explicit semantics

Use existing wall/peak-RSS recording and the smallest prospective evidence sufficient to
test the claimed change. Separate compilation/import/setup allowance from measured steady
state, while counting the phases the actual invocation must pay. Synchronize asynchronous
device work at the declared timing boundary; otherwise dispatch time is not completion time.
Include complete batches, tail batches, allocation, independent validation, merge and I/O
where they belong to the assignment. A kernel-only speedup cannot admit a full publication path.

Report wall time separately from aggregate CPU work whenever parallelism changes the budget
interpretation. Pro must authorize the minimal aggregate CPU measurement needed for such
an assignment under Engineering Scope's existing telemetry restriction; no general telemetry
framework follows. Whole-study contention and effective concurrency remain explicit unknowns
until measured. Do not run automatic worker-count sweeps or repeated timing until a preferred
number appears. A bounded failed engineering assessment returns its actual gap.

Numerical/RNG equivalence follows the scientific claim: use its stated tolerance or exactness,
not a universal bit-identity requirement. A frozen exact census retains all its exact rules;
ordinary A/B exploratory work does not acquire a C-formal obligation from this document.
If dtype, device, batching, reduction order or RNG semantics changes outside its accepted
contract, state that explicitly and obtain the proper scientific decision before using it.

## Reference evidence and the engineering handoff

The source packet provides pinned studies of EPyMARL, MAPPO, BenchMARL, MARLlib, JaxMARL
and Mava, including local navigation overlays under `C:/Projects/ref-lib`. Root will map
each adopted recommendation to the returned core implementation evidence before Pro review.
Their architectures are implementation examples, not measured performance promises for
HMASD. External dependencies not inspected remain declared gaps. Use the referenced commit
and local AGENTS index to reopen the actual code; preserve upstream licenses and instructions
as upstream material, with local navigation clearly marked.

CM records in the existing assignment: complete work/cost law, dominant source locations,
applicable reference pattern, chosen dimensions/topology, protected semantics, resource cap,
verification scope and stop condition. The implementer delivers the smallest complete path
and its actual changed-source scope. The independent reviewer checks full scientific output,
state/RNG/order, real hotspot coverage and honest full-path costing, naming unverified facts.
Correctness and feasibility are distinct; neither a source review nor a rule exception alone
accepts a runtime result. A runtime overrun is engineering evidence, not absence of headroom.

No shortcut may drop a frozen arm, comparator, world, independent check or endpoint to pass
the threshold. Report the whole cost gap and return the appropriate next decision. Previously
completed scientific evidence and object-specific budgets remain intact.

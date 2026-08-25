# Runtime-capacity-invariant continuous roster G32 derivation

Date: 2026-07-25

```text
action=RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_DERIVATION
formal=false
conclusion_bearing=false
iteration_cost=0
iterations_remaining=4
environment=toy
```

## Scope correction

Formal G31 proves that one continuous recurrent policy remains usable while the
active roster changes inside an eight-slot episode. It does not prove that the
same checkpoint can be loaded under a different operational padding capacity.
These are separate capabilities:

```text
within_capacity_dynamic_count != cross_capacity_checkpoint_transport
```

The next action targets only the second capability. It does not reopen G31,
rescue either closed UAV source, or claim arbitrary-N generality.

## Exact counterexamples

### CE-MASK-SHAPE

`ContinuousRosterPolicy.critic[0]` includes `member_capacity` input columns and
`forward_step()` concatenates the complete padded `active_mask`. Likewise,
`FastAnchoredResidualPolicy.slow_critic[0]` includes `member_capacity` columns.
Capacities 8 and 12 therefore produce different parameter shapes, so strict
checkpoint loading fails even though every actor tensor is capacity-independent.

### CE-PADDING-AS-SIGNAL

The raw mask exposes operational slot layout to the critic. Adding four
permanently inactive padding slots changes critic input width and values while
leaving the physical active roster, observations, actions and reward unchanged.
This permits a simpler slot-capacity explanation for any value difference.

### CE-CAPACITY-NORMALIZATION

The current G17 toy writes `active_count / CAPACITY`, capability sums divided by
`CAPACITY`, and a capacity-normalized count into actor/critic inputs. Identical
active records padded to a larger maximum capacity therefore cease to be the
same decision state.

### CE-RETRAINED-SCALE

Training a separate model at each capacity cannot establish checkpoint
transport. A valid test must train one fresh checkpoint, strict-load it at
other capacities with zero optimizer steps, and preserve exact state identity.

## Retained lemmas

- G31's member encoder, context encoder, recurrent actor, action head,
  observation residual, log standard deviation, realized return-to-go target
  and direction-balanced composition have no capacity-shaped parameters.
- Active embedding sum, `log1p(active_count)` and action-prefix fractions are
  already functions of the active roster rather than padded width.
- Runtime observation, hidden, action and noise tensors may have different
  member axes without becoming checkpoint identity.
- The discrete G8--G16 line supplies a constructive pattern: fixed-width critic
  summaries, active sums, log-count and active-fraction prefixes allowed one
  checkpoint to be evaluated with capacities 128/192/224 and active counts
  through 80. Its discrete weights and task are not evidence for G32.
- G31's paired-toy result and both UAV source-non-identifiable results remain
  unchanged.

## Smallest correction

Freeze one representation correction, not a new credit algorithm:

1. base critic input is existing active-set `context_input + critic_state`, with
   no padded mask vector;
2. slow critic input is fixed-width `critic_state + log1p(active_count)`;
3. maximum capacity remains runtime packing metadata and is absent from every
   serialized parameter shape;
4. a new G17-like source uses active capability sums, raw log-count, load,
   target mix and time, never division by maximum capacity;
5. G31 return-to-go, direction balancing, PPO, action factorization, lifecycle
   ownership and RNG rules remain frozen.

## Separating evidence

Train one fresh capacity-8 checkpoint. Strict-load that exact state with zero
evaluation optimizer steps into capacity 6 and 12 instances. Evaluate:

- paired padding: capacity 8 and 12 share the exact `4->3->6->5` active process,
  while four extra capacity-12 slots remain inactive;
- smaller capacity: `4->2->6->3`;
- larger count/churn: `6->3->10->7`.

Every profile contains temporary leave, rejoin, fresh join and terminal leave.
Paired-padding observations on common active rows, value, deterministic action,
reward and lifecycle transitions must be exact. Behavioral access uses the
existing `0.90` utility standard, positive learned gain and the existing
replicate/stochastic stability protections. No UAV field, battery, charging,
failure, geometry or future schedule is admissible.

## Decision

The minimal prototype is the cheapest separating action. Freeze
`RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32` for executable realization,
focused tests and one bounded nonformal CPU exercise. Formal iteration 24 is
not launched until that package is integrated and its evidence contract passes.

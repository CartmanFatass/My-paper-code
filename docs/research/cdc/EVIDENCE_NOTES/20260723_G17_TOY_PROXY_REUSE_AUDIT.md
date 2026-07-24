# G17 toy-proxy reuse audit

Date: 2026-07-23

## Question

After the heavy UAV G1 operational timeout, what existing toy code can be
reused for the next algorithmic action without reopening a closed source or
mislabeling tensor compatibility as scientific compatibility?

## Rejected direct reuse

The exact Iteration-5 `SpatialDynamicRosterEnv` is not an admissible G17 source.
It was validly closed as `RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS` under its
registered learner, budget and gates. The new autonomous grant does not turn a
closed carrier into a fresh result merely by renaming it or changing the
autoregressive prefix.

The G8 network and that carrier happen to share `observation_dim=15` and three
primitive actions, but their meanings differ:

- spatial field 7 is the wave target, while the G8 training carrier uses it for
  short-completion state;
- spatial field 11 is physical position, while the G8 training carrier uses it
  for lifecycle active steps;
- spatial actions mean left/stay/right, while the G8 checkpoint was trained on
  idle/persistent/short allocation.

Consequently, a G8 checkpoint can load and execute mechanically yet cannot
produce valid zero-shot G8 evidence on that carrier. Such a score would be an
uncontrolled channel/action-semantic substitution.

## Reusable implementation primitives

The following code is reusable because it does not carry the retired task
claim:

- lifecycle-owned hidden-state freeze/restore/delete mechanics;
- active-only observation packing, active masks and anonymous frontier order;
- active-set sum, `log1p(active_count)` and active-fraction autoregressive
  representation;
- replay, PPO, checkpoint and deterministic RNG utilities;
- ledger construction patterns and proof-sized lifecycle invariants.

The old spatial environment and its formal result may be used only as a
counterexample and implementation reference, never as the new evidence source.

## Smallest next boundary

Define a new lightweight continuous service-roster toy carrier, rather than a
modified copy of the retired discrete carrier. It should retain the accepted
dynamic-lifecycle spine and G8 representation, use fresh semantically named
observation channels and continuous service-allocation actions, and train from
scratch. Its dense external task utility must first pass a bounded source/access
prototype before any formal evidence contract is frozen.

This proxy may test whether the accepted dynamic-roster representation remains
usable when the primitive control family becomes continuous. It cannot itself
be reported as UAV evidence; Scenario 7 remains a later PM promotion target.

```text
next_boundary=CONTINUOUS_SERVICE_ROSTER_PROXY_G17_EXECUTABLE_DEFINITION
implementation_status=not_started
formal_compute_status=standing_user_grant_not_launchable_until_evidence_contract
conclusion_bearing_iteration_cost=0
toy_first_chain_iterations_remaining=10
```

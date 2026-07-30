# The corrected replay gate passes, and the mechanism it tests actually fired

Date: 2026-07-30
Instruments: `scripts/d7_s_manifest_replay_probe.py`, `scripts/d7_s_manifest_replay_gate.py`
Manifest set: `manifests/d7s_dev/`, committed, `set_hash 0212ef4613fb5974c9...`
Topology: `TOPOLOGY_SEED_DEV = 20260725`. **No R4 topology was constructed.**

## Result

```text
MANIFEST_REPLAY_PASS
independent executions: True -- pid differs
all 1 episode(s) replayed identically across independent executions,
over the registered stable and flex horizons
```

Every one of the ruling's eight assertions is now satisfied on this vehicle, where
the previous run failed assertion 6.

## The check that mattered more than the verdict

A PASS here would have been worthless if the post-initialization trigonometric
writers never ran — the equality would then say nothing about the exact risk A1
exists to test, and this project has already been burned once by a rate reported
without confirming its mechanism fired.

```text
post_manifest_user_waypoint_regenerations     53
post_manifest_cluster_target_regenerations   170
continuation_stable_steps                    139   (= H_STABLE)
continuation_flex_steps                      550   (= H_FLEX)
event_found                                 True
unit_stable_invalid / unit_flex_invalid    False / False
replaced_a_different_world                  True   (both sides)
```

**The generators fired 223 times across the exercised continuations.** The
equality is therefore over trajectories that really did re-enter `np.cos`/`np.sin`
after initialization, which is what the ruling's Gap 3 asked for:

> If all relevant generators remained dormant, equality would leave the exact
> A1-versus-A2 risk untested.

`replaced_a_different_world=True` on both sides matters equally: each execution
started from a *different* construction-time world, so the agreement is replay and
not a coincidence of two identical starting states.

## What changed since the failing run

```text
a6_complete_pre_step_environment_identity   False -> True
canonicalization_barrier_present                     True
derived_state_rebuilt      _reset_connection_baseline, _update_channel_state,
                           _update_uav_connections, _compute_routing_paths
```

The barrier is `canonicalize_post_pin_initialization()` on the Scenario 7 env, and
the assertion now fires at the ruling's boundary — after the energy permutation and
the canonicalization, before the first action — rather than at an intermediate
state the episode never steps from.

Measured independently of the implementing agent, over four construction pairs:

```text
pairs agreeing on full_state_fingerprint BEFORE the barrier   0 / 4
pairs agreeing AFTER the barrier                              4 / 4
RNG token unchanged by the barrier                            4 / 4
nine world arrays unchanged by the barrier                    4 / 4
```

**Both stale families converge, including `current_graph_potential`** — which this
project's previous note recorded as surviving a station-only recompute, and which
was the evidence that the station-only repair the ruling rejected would not have
been enough.

## What this does NOT establish

- **Cross-machine replay.** Both executions were local processes; the gate reports
  independence from `pid` and says so. Under the ruling this is sufficient to
  continue development work and **not** sufficient to select A1, wire the manifest
  into the audit path, bind a fresh inventory, or authorize a formal result.
- **That A1 suffices.** Two processes shared one runtime. The question A1 asks is
  whether horizon equality survives a *different* runtime.
- **That one episode generalizes.** One topology, one episode, one event.
- **The `user_cluster_assignments` divergence**, open since round 2 and still
  unexplained: the value is an integer written as `cluster_idx` or by an explicit
  `np_random.choice`, both branches consume a fixed number of draws, so an aligned
  stream should not produce a differing assignment.

## The remaining step is gated, not unfinished

`manifests/d7s_dev/` is committed and verifies in place — the repository copy
returns the same `set_hash` as the machine that froze it, so the bytes two runners
would load are provably the frozen bytes. What is missing is a cloud job to run
them, and workflow-file pushes are user-gated on this line.

The exact job is written out in
`docs/project/PROPOSED_WORKFLOW_JOB_MANIFEST_REPLAY.md`, together with the reason
it could not ride an existing job: `benchmark` has a 30-minute timeout and already
spends 900 seconds on the conformance search, and making the probe fit would mean
quietly changing what a job named `benchmark` measures.

Recorded as an escalation rather than worked around, per the ruling's own warning
against indefinite operational loops on a vehicle that cannot answer the question.

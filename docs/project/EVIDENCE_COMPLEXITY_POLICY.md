# HMASD evidence and scaling complexity policy

```text
policy_kind=user_authorized_hard_workflow_boundary
purpose=test_external_pro_ideas_without_unbounded_search
search_complexity_ceiling=O(H*K_search)
candidate_trajectory_count_ceiling=16
future_simulated_transitions_per_controller_episode<=16*H
candidate_count_independent_of_episode_horizon=true
nested_rollout_replanning=forbidden
nonformal_wall_clock_cap_minutes=20
formal_iteration_wall_clock_cap_hours=8
scalable_algorithm_target=O(N*k_neighbor)_or_O(N*logN)
neighbor_count_ceiling=16
dense_pairwise_deployment_claim=forbidden
fixed_small_exact_simulator_O(N^2)=allowed_as_reference_only
override_authority=user_only_for_one_named_boundary
violation_iteration_cost=0
```

`H` is the registered episode horizon. `K_search` is a fixed, explicitly
listed set of hypothetical trajectory candidates and may not grow with `H`.
The transition budget counts hypothetical environment transitions introduced
only to search, rank or certify an idea; it does not count the one real evidence
trajectory, ordinary simulator physics, a policy forward pass or direct
non-trajectory algebra.

## Evidence-search ceiling

Allowed evidence tests may directly score at most 16 fixed candidates per
boundary without advancing hypothetical environments, or roll out at most 16
fixed candidate trajectories once per controller episode. Their combined
hypothetical transitions may not exceed `16*H`. A constant-depth local probe is
also allowed inside the same bound.

The following are forbidden even if native code or more cores make one small
instance finish:

- replanning at every real step by rolling every candidate through the
  remaining horizon;
- invoking a rollout/search controller recursively inside its candidate
  rollout;
- exhaustive `time x candidate x remaining-horizon` enumeration;
- tree search, beam search, MCTS or an equivalent expanding trajectory search;
- a candidate library whose size grows with episode horizon;
- using implementation optimization to excuse an asymptotic violation.

Evidence search may be linear in `H` times fixed `K_search`. `O(H^2*K_search)`,
`O(H*K_search^2)`, exponential search and unbounded adaptive enumeration are
outside this project. Prefer an analytic bound, constructive witness, paired
intervention, toy counterexample or one precomputed plan.

## Agent-count scaling

This is separate from evidence search. A small exact simulator may retain dense
all-pairs communication or interference at `O(N^2)` as a reference when its
registered fleet size is fixed. Native batching, vectorization, incremental
recomputation and C++ are encouraged on that valid path.

An algorithm presented as scalable to changing agent count may not introduce a
dense pairwise deployment path. Its target is bounded-neighborhood
`O(N*k_neighbor)` with `k_neighbor<=16`, or `O(N*logN)` hierarchical/spatial
aggregation, with linear or near-linear memory. Spatial cutoffs, sparse graphs,
low-rank kernels, FMM-like aggregation or learned neighbor selection can reduce
complexity, but any approximation of physical links or interference is a new
scientific assumption and must receive its own design audit and error/result
check. The exact `O(N^2)` simulator remains the reference oracle, not the
claimed scalable algorithm.

## Prelaunch gate

Before a Pro-proposed evidence action is frozen or implemented, Project Manager
records a zero-compute upper bound for candidate count, hypothetical
transitions and asymptotic complexity. When constants are unknown, PM may run
one microbenchmark lasting at most 20 minutes. The complete nonformal exercise
must finish within 20 minutes on the registered local CPU. The cumulative wall
clock for one formal train/evaluate/analyze iteration, including resumes, must
be projected to and capped at eight hours on that machine.

A violation is `NON_EXECUTABLE_EVIDENCE_DESIGN`, not a scientific result or a
failed iteration. PM stops implementation at the smallest reproducer and asks
External Pro for a cheaper separating idea inside this policy. Pro supplies
ideas and scientific distinctions, not an unlimited solver. Neither an active
grant nor formal-compute authority overrides this policy; only the user may
grant one named exception with a replacement bound.

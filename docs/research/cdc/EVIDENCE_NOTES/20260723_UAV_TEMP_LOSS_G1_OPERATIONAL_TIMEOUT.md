# UAV temporary-loss G1 operational timeout

Date: 2026-07-23

## Terminal mechanical facts

```text
source_family=UAV_TEMPORARY_SERVICE_LOSS_G1
source_commit=b125efd205e302666aea78b286d6857f8ecf9286
run=logs/formal_uav_temp_loss_g1_cpu_20260723_b125efd_r1
phase=TRAIN_SOURCE_SCREEN
first_attempt_exit=timeout_after_7200313_ms
authorized_retry_exit=timeout_after_7200444_ms
process_live=false
launch_identity_present=true
source_screen_launch_identity_present=true
committed_control_chunks=0
train_manifest_present=false
source_screen_present=false
evaluation_manifest_present=false
analysis_result_present=false
progress_present=false
```

The registered experiment operator returned `ERROR` after the original
foreground command and its one authorized exact retry both reached the two-hour
command boundary. No terminal scientific artifact exists and no result branch
is admissible.

## Scientific and iteration disposition

This is an operational failure, not evidence for source non-identifiability,
learned access, mask sufficiency or dynamic-lifecycle benefit. Iteration 18 was
not consumed and no Chinese iteration report is created.

The preceding bounded exercise already warned that the constructive controller
did not clearly dominate no reallocation, so another multi-hour execution of
the same heavy source is not the cheapest separating action. The user has also
frozen algorithm discovery to the previous toy environment, with Scenario 7
reserved for PM-promoted candidates.

## Performance disposition and successor

Three exact-semantics UAV fast paths were accepted and integrated at commit
`61e9704`: exact communication-state caching, raw step-view reuse, and graph
radio/topology reuse. The final six-seed paired 3-step benchmark improves median
runtime by `36.662707%` with exact transition equality and 55 focused tests
passing. A separate fused controller-worker prototype improved only `0.829483%`
and was removed.

The G1 scientific question remains open but deferred; it is not renamed,
rescued or treated as a failure result. The active research loop returns to a
small spatial service-roster toy proxy before any later UAV promotion.

```text
next_boundary=SPATIAL_SERVICE_ROSTER_PROXY_G17_DERIVATION
conclusion_bearing_iteration_cost=0
toy_first_chain_iterations_remaining=10
uav_g1_rerun_status=not_selected
```

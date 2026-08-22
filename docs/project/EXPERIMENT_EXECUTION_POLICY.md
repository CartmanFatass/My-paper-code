# Experiment Execution Policy

Result-bearing execution is an R2 boundary. The route, backend, parallel
state, resource preflight, manifest, measurement sample, and direct consumer
are recorded before launch.

There is no project-wide default or hard upper limit for worker/environment
count. Every launch width is selected by CM from a current CPU/memory preflight
for the exact host and route. A number in a neighbor-count or evidence-candidate
policy is not a worker count. Per-worker Python/Torch threads remain one where
the registered CPU contract requires it.

When a semantics-preserving registered C++ backend exists, a result-bearing run
must use it and parallel execution. Python/serial is allowed only for
`DEBUG_REFERENCE` or `REFERENCE_ORACLE` with `result_bearing=false`. No silent
fallback is permitted. Missing native wiring is CM implementation work and
routes to E2 recovery; it is not a scientific stop.

Before a runtime/cost conclusion, warm up the exact route and measure at least
500 environment steps or five seconds, recording steps, updates, evaluations,
backend, workers, threads and build mode. Runtime profiles are engineering
review thresholds, not scientific termination conditions.

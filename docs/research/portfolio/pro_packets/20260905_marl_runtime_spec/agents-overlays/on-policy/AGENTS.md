# Local HMASD navigation overlay

This file is an additive local navigation record for the upstream `marlbenchmark/on-policy`
snapshot at commit `de66d7a4b23fac2513f56f96f73b3f5cb96695ac`. It is not upstream project
documentation. No upstream `AGENTS.md` existed at this path in the fixed checkout. Keep the
Python source read-only for this survey; only navigation overlays and the sibling report tree are
in scope.

Key areas: `onpolicy/runner/` owns rollout/update orchestration, `onpolicy/envs/` owns wrappers and
environment adapters, `onpolicy/algorithms/` owns policy/trainer code, `onpolicy/utils/` owns
NumPy replay buffers, and `onpolicy/scripts/train/` owns entry points. Evidence is recorded under
`C:/Projects/ref-lib/reports/on-policy/`.

# ACVC history-headroom R01 engineering blocker

Status: **INCOMPLETE_ENGINEERING_BLOCKER / DO_NOT_INTEGRATE**

This branch preserves a reproduced engineering diagnostic from science-card commit
`397205f76c78a6c3ab9c2a990b43da16745395d4`. The formal horizon-12 invocation was not run, no
scientific result root or HR branch was produced, and these bytes must not be merged or
cherry-picked into the DM, CM, or primary branch.

The implementation is an exact rational Python path: exact likelihoods and posteriors, unchanged
DET-CF action semantics, exact action tie order, no truth after VETO, exact alpha-envelope Bellman
backup without a posterior grid/tolerance/approximate pruning, and exact forward reporting. It is
retained because it reproduces the cost gap; it is not a launchable implementation.

## Reproduced facts

The exact main-value prefix produced:

| horizon | retained alpha vectors | main-value wall |
| ---: | ---: | ---: |
| 1 | 8 | 0.0110 s |
| 2 | 137 | 0.1717 s |
| 3 | 1,413 | 3.1022 s |
| 4 | 10,375 | 38.5775 s |
| 5 | incomplete | still running at 115 s; terminated before the 120 s formal cap |

The horizon-12 calculation must first complete horizons 1 through 12 and then emit exact forward
metrics, the visible-history witness or certificate, and the probability-weighted forced-DET
Q-advantage with the continuation re-optimized at every exact legal posterior. Because horizon 5
alone did not finish within 115 seconds, this path cannot meet the frozen 120-second invocation
cap. The formal horizon-12 path was never invoked.

The focused suite was run once from the repository worktree:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD-worktrees/impl-acvc-history-headroom-r01-20260904/temp/directions/acvc/test/history-headroom-alpha-r01 tests/experiments/candidates/acvc/history_headroom_r01
```

Observed result: `16 passed`, one existing repository pytest-configuration warning, `18.36 s`.

That suite's reduced-horizon subprocess ran this exact technical-only command:

```powershell
C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe C:\Projects\HMASD-worktrees\impl-acvc-history-headroom-r01-20260904\scripts\run_acvc_history_headroom_r01.py --output-root C:\Projects\HMASD-worktrees\impl-acvc-history-headroom-r01-20260904\temp\directions\acvc\test\history-headroom-alpha-r01\test_reduced_horizon_toy_publi0\run --admission-receipt C:\Projects\HMASD-worktrees\impl-acvc-history-headroom-r01-20260904\temp\directions\acvc\test\history-headroom-alpha-r01\test_reduced_horizon_toy_publi0\admission.json --toy
```

The H3 publication was technical-only and selected no scientific branch. It recorded `7.4621792 s`
wall time, `27,516,928` bytes peak RSS, exact alpha counts `{0: 1, 1: 8, 2: 137, 3: 1413}`,
and an exact positive-mass history witness.

## Known defects

1. The 120-second wall cap is checked only after Bellman and forward calculation. A formal call
   would overrun rather than stop during recursion and publish only HR-X/no-observation evidence.
2. The summary adds work-unit and wall-seconds-per-work-unit performance telemetry. The card
   authorizes only wall time and peak RSS plus its required Bellman/normalization counts, so this
   extra telemetry violates engineering-scope section 4.

The forward exact-belief occupancy also retains exponential growth and has not been replaced by a
bounded exact policy-plan evaluation. Repair requires a materially different exact algorithm with
a demonstrated horizon-12 resource bound; weakening exactness, recursion coverage, information
boundaries, witness semantics, or the Q-advantage observable is not an admissible repair.

No engineering-scope section 4 machinery is authorized for a future repair (`scope: none`).

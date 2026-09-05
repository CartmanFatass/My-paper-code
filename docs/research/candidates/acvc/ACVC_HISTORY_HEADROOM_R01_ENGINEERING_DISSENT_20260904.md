# ACVC history-headroom R01 — engineering dissent

- Direction: `acvc`
- Frozen object: `ACVC-A-RECON-HISTORY-HEADROOM-R01`
- Status: **ENGINEERING_DISSENT / DIRECTION_DECISION_REOPEN_REQUIRED**
- Original decision: `PRO_FINAL / RECAST_HEADROOM_FIRST`
- Science-card commit: `397205f76c78a6c3ab9c2a990b43da16745395d4`
- Diagnostic implementation commit: `5e0fdbfd68af381ede7f212364d94457faa4a2f1`
- Diagnostic branch: `codex/impl/acvc-history-headroom-r01-20260904`
- Diagnostic marker SHA-256:
  `09723670f1801633c9e426d02a3d3ad24ecdfedfc9217cf747328af775319def`

## Missing engineering fact

The Convergence decision admitted an exact horizon-12 finite-support Bayes/dynamic-program
calculation under a 120-second wall cap and 1.5-GiB peak-RSS cap. A bounded CM chain implemented two
exact rational algorithms and reproduced that the main-value calculation alone cannot reach
horizon 12 under the frozen wall cap. The formal result invocation was never launched.

The final exact alpha-envelope prefix measurements were:

| horizon | retained exact alpha vectors | main-value wall time |
| ---: | ---: | ---: |
| 1 | 8 | 0.0110 s |
| 2 | 137 | 0.1717 s |
| 3 | 1,413 | 3.1022 s |
| 4 | 10,375 | 38.5775 s |
| 5 | incomplete | still running at 115 s; terminated before the 120 s cap |

Horizon 12 would additionally require horizons 6–12, exact forward consequence metrics, the
receiver-visible history witness or certificate, and the probability-weighted forced-DET
Q-advantage with continuation re-optimized at every exact legal posterior. An earlier direct
belief-recursion implementation already required 6.85 seconds and 2,525 terminal beliefs at
horizon 3. The exact alpha representation removed that value-recursion duplication, but its own
prefix growth still crosses the invocation cap before horizon 5 completes.

## Reproduction and recorded bytes

The independent diagnostic branch preserves the exact incomplete implementation, runner, tests,
and a `DO_NOT_INTEGRATE` marker. It is pushed and clean; it is not an ancestor of the DM branch and
must not be cherry-picked. File hashes are:

| file | SHA-256 |
| --- | --- |
| `experiments/candidates/acvc/history_headroom_r01/INCOMPLETE_ENGINEERING_BLOCKER.md` | `09723670f1801633c9e426d02a3d3ad24ecdfedfc9217cf747328af775319def` |
| `experiments/candidates/acvc/history_headroom_r01/__init__.py` | `0dc7eedbed8cb2bb6afb2ec14695e1d56b86ea9bbe5a8d3645cee1f59e2e10b8` |
| `experiments/candidates/acvc/history_headroom_r01/experiment.py` | `c10e887c2b72b8a70e065eae8a5e1324d2fbe1924ac9559dc7c961876083975c` |
| `scripts/run_acvc_history_headroom_r01.py` | `328a6118a74324ca292bc2717d893448ec5da1e8c38aa917d732f3c19e77f1d4` |
| `tests/experiments/candidates/acvc/history_headroom_r01/test_history_headroom.py` | `3982b7b33ee5d1e740564d0e414595982b2607c660f05c7269620d5d69b1d96c` |

The focused suite command and exact reduced-horizon technical command are recorded in the marker.
The suite produced `16 passed` in 18.36 seconds. Its horizon-3 technical-only publication took
7.4621792 seconds and 27,516,928 bytes peak RSS, recorded alpha counts `{0:1, 1:8, 2:137,
3:1413}`, and selected no scientific branch. No new calculation was run when the diagnostic branch
was committed.

CM and an independent reviewer checked the exact alpha envelope, rational tie order, information
boundary, no-truth-after-VETO transition, unchanged DET-CF parity, forced-DET continuation
re-optimization, witness semantics, harm metrics, and result-rule code. They found no correctness
contradiction in those seams. The reviewer independently confirmed that no small local exact
optimization closes the horizon-5-to-12 gap inside 120 seconds.

## Why the partial implementation is not acceptable

Besides the capacity gap, the preserved partial diff has two material engineering defects:

1. it checks the 120-second cap only after Bellman and forward calculation, so a formal call would
   overrun instead of stopping at a clean boundary; and
2. it persists work-unit and seconds-per-work-unit telemetry beyond the card-authorized wall time,
   peak RSS, Bellman counts, and normalization receipts, breaching engineering-scope section 4.

The forward exact-belief occupancy also retains exponential growth. Repair therefore requires a
materially different exact algorithm with a demonstrated horizon-12 resource bound, not acceptance
of the partial diff. Approximation, posterior grids, tolerance pruning, information leakage,
omitted observables, relaxed witness/Q semantics, or a silent cap extension would change the frozen
object.

## Classification and scientific boundary

This is a reproduced **engineering admission blocker**. It is not `HR-X`, because no formal
result-bearing horizon-12 invocation was accepted and no result root exists. It is not `HR-A`,
`HR-B`, `HR-C`, or `HR-D`; it supplies no headroom polarity. The A/RECON object has no consumption
state in any event. No learner is admitted, and B1/R01 remain closed at their prior exact units.

An unavailable implementation or costly exact calculation cannot become a scientific negative.
The direct observations above bound only the current exact implementations under the frozen
resource contract.

## Direction-tier decision reopened

Changing the horizon, exactness requirement, complete-state coverage, observables, wall/RSS cap,
or policy class changes frozen scientific meaning and is not an object-tier repair. The same
`em:acvc:convergence` node must reconsider the direction with this missing engineering fact.

Options for the reopened node are:

- **RECAST_FEASIBLE_EXACT:** specify a new, scientifically meaningful exact discriminator whose
  resource feasibility is established prospectively without using the technical horizon-3 output
  as scientific polarity;
- **RECAST_CERTIFIED_BOUND:** replace the exact full value with a prospectively frozen exact
  threshold certificate or bound that preserves a competent legal action/native-return question
  and all required consequence semantics;
- **PARK_ENGINEERING_DEPENDENCY:** park ACVC until a materially different exact algorithm has a
  result-blind horizon-12 cost/RSS demonstration inside the existing cap; or
- **CLOSE_DIRECTION:** close only if the scientific evidence, rather than this engineering cost,
  supports closure.

DM recommendation: **PARK_ENGINEERING_DEPENDENCY**, unless the node can specify a class-correct,
resource-admitted exact recast without adding prohibited machinery. The current data do not justify
closure, a cap increase, approximation, or a learner ladder. The direction is parked at this clean
boundary pending a complete reopened decision; a connector or transport blocker would form no
decision.


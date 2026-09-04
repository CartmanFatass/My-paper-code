# FRRIE B01 CM engineering milestone — 2026-09-01

## Current engineering conclusion

The package-native toolchain is now directly established. B01 has real MSVC/native A/RECON
evidence, exact scalar/batch and 1/2/4-worker equivalence, one actual width-32 two-arm collector
assessment, paired training/checkpoint primitives, and candidate validators for the frozen panel.
It still has no valid B01 scientific result.

Production remains **`REPAIR_REQUIRED`**. The sole direction-level readiness blocker is
`FULL_PANEL_RUNNER_AND_FULL_CHAIN_TELEMETRY_INCOMPLETE`: there is no complete 512-update production
orchestrator, no complete 98-cell-per-seed evaluation publication, and no atomic whole-panel
artifact binding the ordered shadow, between-arm action-TV, parameter-distance, process-tree, and
all 28 frozen quantities. The current source is also dirty and uncommitted, so the formal source
gate correctly refuses a result-bearing launch.

## Direct non-result observations

### Package-native A/RECON

The authoritative retained root is
`temp/frrie_b01_a_recon_native_23472_1788271030978261200/`.

- `vcvars64.bat`:
  `C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat`.
- Compiler:
  `C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe`.
- The retained native artifact is 120,320 bytes.
- All 48 scalar/batch direct rows are equal.
- All 24 worker rows are equal across requested worker counts 1, 2, and 4.
- End-to-end telemetry records 6.875 seconds wall, 9.9375 seconds CPU, 290,942,976 bytes
  process-tree peak RSS, four peak processes, and 54 peak threads.
- The artifact is `test_only=true`, `result_bearing=false`, and `scientific_values=null`.

This closes the old missing-toolchain and primitive-equivalence blocker. It does not prove that a
production full-seed runner uses four workers effectively.

### Actual width-32 collector assessor

The retained assessor is
`temp/frrie_b01_batch_assess_20260901_052900/assessment.json`.

- Fresh physical/effective memory at admission: 16,422,092,800 bytes.
- Both arms collected exactly 4,928 environment slots, for 9,856 total slots.
- Each arm records 768 factual slots, 1,248 factual-suffix audit slots, and 2,912
  nonfactual-suffix slots.
- Paired exogenous receipts and factual replay traces are directly equal, and model bytes remain
  unchanged during collection.
- Collector wall time is 11.6354654 seconds, or about 847.07 slots/second.
- End-to-end telemetry records 17.079 seconds wall, 21.609375 seconds CPU, 386,351,104 bytes
  process-tree peak RSS, four peak processes, and 55 peak threads.
- The retained assessor's per-stage labels are historically swapped. Only the end-to-end totals
  and the collector's own wall/slot measurements are authoritative; current code has corrected the
  stage transition order without rewriting the old artifact.

The assessor is TEST-only and has no optimizer step, seed packet, production root, or scientific
value. Its direct blocker is that the shared-model collector uses one caller; production workers4
must be realized at independent seed work, not by concurrent mutation of one model.

## Implemented scientific-contract boundary

The B01 namespace binds the exact experiment
`FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901`, CPU/FP32 model compute, float64 analysis
reductions, the package C++ width-32 batch ABI, fixed RSCF loss, one Adam step per update, and
post-Adam projection with optimizer moments unchanged.

The paired transaction rolls both arms back on any failed update or postcondition. Before first
tight-box contact, model/optimizer state and all policy-derived training information must match.
After contact, endogenous observations, actions, targets, and model-derived quantities may differ;
the invariant retains common addressed tapes, law revisions, roles/masks, origin addresses, and
exact work.

Two complete Innovator clarifications are now implemented prospectively:

- between-arm action-TV is the symmetric two-anchor descriptive diagnostic and never a gate;
- parameter distance uses every post-projection update from first tight contact through 512,
  with the exact 35,513-element state layout, authoritative paired raw state bytes, and separate
  full/beta/non-beta L-infinity distances. It is also descriptive and non-gating.

Formal parameter-distance availability derives first contact from revalidated paired 512-update
training shards. Caller-supplied contact indices are restricted to explicit TEST/component paths.
Complete-panel analysis remains fail-closed.

## Quarantined integrated-smoke attempts

Three fresh, non-result TEST attempts exposed integration defects. All are retained only as
`*.incomplete`; none consumes the B01 scientific object, and none may be interpreted,
resumed, salvaged, or used as a result source.

1. `temp/frrie_b01_integrated_one_update_test_20260901_01.incomplete/` stopped before the optimizer
   because paired Q-target equality used numeric `torch.equal` on canonical illegal-action FP32
   NaN sentinels. The repair now requires exact masks, finite bit-equal legal targets, and exact
   canonical NaN payloads on illegal positions. A full fake-environment collector-path regression
   and the independent reviewer accept this outcome-blind repair.
2. `temp/frrie_b01_integrated_one_update_test_20260901_02.incomplete/` passed fresh admission and
   reached post-update artifact validation, where the validator incorrectly required bit equality
   between `mean(per-episode composite loss)` and a recombination of separately averaged
   components. FP32 non-associativity makes that identity invalid. Repair is restricted to
   preserving and replaying the original left-fold/division reduction and exact serialized bits;
   it must not change training arithmetic. Root integrated and pushed that independently CLEAN
   repair as commit `1fc04ab3` before authorizing the next attempt.
3. `temp/frrie_b01_integrated_one_update_test_20260901_03.incomplete/` used committed source and
   passed fresh admission, collection, update, and most final validation. The remaining validator
   duplicated the native waste derivation with Python binary64 integer division, while the C++ ABI
   and producer define waste through FP32 operands and division. Legal non-exact ratios such as
   `1/3` therefore failed exact comparison. The repair introduces one authoritative
   primitive-to-return helper shared by the batch producer and artifact validator. It validates
   count support, reproduces the C++ FP32 waste bits, derives the binary64 endpoint once, and can
   validate an observed return exactly. The old duplicated binary64 ratio and endpoint arithmetic
   are removed.

The three fresh receipts recorded physical/effective availability of 14,999,437,312,
14,731,214,848, and 15,404,646,400 bytes respectively. All passed the 4 GiB admission floor. In
every case the final name was absent after failure and the package `_native` directory was clean.

## Verification state

The arithmetic repair is independently **CLEAN** and commit-ready as a non-result milestone. It
preserves the original single graph pass and exact 64-episode Python/Torch FP32 left-fold order,
records all per-episode component bits plus aggregate bits, and replays that exact reduction in the
integrated and direct-512 validators. The reviewer also confirmed strict built-in integer/range
checking for aggregate bit words and rejection of Boolean or nonfinite aggregate scalars.

The final bounded B01 suite is `94 passed, 3 deselected`; the deselected cases are actual/native
invocations and were not silently counted as evidence. Focused checks include:

- integrated root/cleanup/quarantine contract: `6 passed`;
- parameter-distance contract: `11 passed`;
- canonical collector-path illegal-NaN parity regression: `1 passed, 4 deselected`;
- paired trainer focused regression: `6 passed`.
- arithmetic, projection, Boolean/u32 range, nonfinite, and tamper regression: independently CLEAN;
- direct-512 reduction schema: `1 passed`;
- CM trainer/integrated independent run: `13 passed`.
- authoritative primitive-to-return FP32 round trip and tamper regression: `7 passed` integrated,
  `4 passed, 1 deselected` batch static, and reviewer-independent `1 passed`.

The reviewer returned **CLEAN** for the primitive repair and found no material issue. No `_04`
smoke is authorized or required for this commit-ready non-result milestone.

## Remaining production work

1. Root must integrate the CLEAN primitive-to-return repair into a commit-bound milestone. Do not
   launch another integrated smoke as a substitute for the full production chain.
2. Implement one atomic full-seed runner for all 512 updates with checkpoint restore inventory and
   actual four-worker seed-level orchestration.
3. Publish all 98 adaptation-free evaluation cells per seed and the exact ordered-shadow,
   action-TV, and parameter-distance raw rows required by the prospective contracts.
4. Bind complete process-tree wall/CPU/RSS/process/thread/I/O telemetry, scratch/durable high-water,
   and create-once/quarantine behavior to the full chain.
5. Validate the complete panel and every frozen quantity, then run an independent source/readiness
   review against one committed clean revision.
6. Only after all preceding gates are CLEAN may a fresh 4 GiB admission precede the initial three
   result-bearing seeds.

For scale, one seed contains 2,523,136 training slots per arm, or 5,046,272 paired-arm slots. The
three-seed initial phase contains 15,138,816 paired-arm slots. These static counts are not runtime
feasibility or scientific evidence.

## Scientific status and next decision

There is no new valid algorithm observation and no direction-local Convergence trigger. The claim
ceiling remains a preliminary finite-budget comparison of the tight projection/optimizer package
against its containing package on the literal three- or five-seed panel. Convergence is triggered
only after a valid complete initial three-seed B01 panel; TEST, A/RECON, incomplete, and technical
artifacts do not trigger it. Direction advice remains **continue / ACTIVE**, without a Portfolio
lifecycle change.

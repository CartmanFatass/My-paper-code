# VNFC BPCR B/EXPLORE R01 engineering milestone

## Current disposition

`VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R01` has passed the independent A–G,
bounded thin-CLI, and load-only native-binding reviews. The runner now declares
`IMPLEMENTATION_READY = True` for the single frozen DEBUG pilot.

The production path has performance disposition `PILOT_ONLY`: one frozen eight-update DEBUG may
run only after the final READY flip and a fresh 4 GiB admission. Its process-tree telemetry must
measure wall time, CPU, peak RSS, scratch and durable high-water marks, I/O, and scientific-work
throughput. PRIMARY and OPTIONAL remain unavailable until a valid archived DEBUG three-piece
bundle is accepted. Static tests do not establish scientific polarity or production performance.

The final non-result regression contains 102 passing tests. No formal DEBUG, PRIMARY, OPTIONAL, or
other result-bearing endpoint was run during implementation.

## Closed engineering contracts

- The registered R09 primary remains the only authority for trajectory, action, and return. The B
  shadow is a deterministic, read-only same-input/action replay. Its raw-tick latency is a direct
  shadow observation; applicability to primary is an inference allowed only when every boundary,
  source identity, and native artifact identity is exact.
- PS-B0 constructs 18 actual-path states and four distinct active presentations, then persists all
  288 initial/debug-final MAPR/DIRECT comparisons with score/probability diagnostics. It tests
  opaque deterministic support and explicitly makes no equal-logit claim.
- Runtime validation binds every paired receipt to its exact training arm/update/roster or
  evaluation cell/checkpoint/arm. DEBUG requires four primary-only N7 sensitivity calls, twelve
  primary-only BCRH calls, and the separate 24-call PS-B0 ledger.
- Durable publication is monotonic and create-once. A valid run consists only of scientific
  `RESULT_BODY.json` plus observer `TELEMETRY_TERMINAL.json` and `VALID_CLAIM.json`. A pre-seal
  failure preserves all partial bytes, appends `INCOMPLETE.json`, seals the partial inventory, and
  publishes only `TELEMETRY_TERMINAL.json` plus `INCOMPLETE_CLAIM.json`. Post-seal observer failure
  cannot change the scientific root and creates only `OBSERVER_INCOMPLETE.json` in the publication
  namespace. Legacy `RESULT.json`, `OUTCOME_CLAIM.json`, rollback deletion, and post-hoc artifact
  registration seams are absent.
- Recovery is recomputed from retained raw ticks. BCRH, sensitivity, DIRECT activity, exact host
  calls, source/native bindings, checkpoint identities, and process/storage telemetry are
  cross-validated rather than accepted from summary booleans.

Old R09 code and tests have zero content diff. Its full historical suite still has pre-existing
canonical-EOL manifest failures in this checkout; the B/EXPLORE change neither edits nor repairs
that frozen surface.

## Construction-only PS-B0 readiness command

Use the project interpreter and create a fresh admission receipt immediately before the command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out 'temp/vnfc-bexp-r01/ps-b0-readiness-preflight.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_vnfc_bpcr_b_explore.py ps-b0-readiness --preflight-receipt 'temp/vnfc-bexp-r01/ps-b0-readiness-preflight.json'
```

This is construction-only and non-result-bearing. It reads the admission receipt once, requires
the existing content-keyed primary and shadow DLLs without building them, constructs and closes the
18 in-memory native states, and prints one canonical JSON receipt with the exact 24-call ledger to
stdout. It creates no RNG master, Torch model, optimizer, checkpoint, scientific/durable root,
publication root, terminal, or result. Its only disclosed runtime effects are loading the prebuilt
native libraries and constructing temporary in-memory host state.

Formal PS-B0 must not be run separately. It uses the initial and same-invocation debug-final
checkpoints inside the frozen DEBUG command below.

## Frozen formal DEBUG command

Choose three new, empty, pairwise-disjoint roots. The durable root must be the exact named
scientific namespace shown here; the publication root is a separate observer namespace.

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out 'temp/vnfc-bexp-r01/debug-2026090101-preflight.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_vnfc_bpcr_b_explore.py debug --stage B0-DEBUG --seed 2026090101 --updates 8 --preflight-receipt 'temp/vnfc-bexp-r01/debug-2026090101-preflight.json' --scratch-root 'temp/vnfc-bexp-r01/debug-2026090101-scratch' --durable-root 'temp/vnfc-bexp-r01/VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R01/B0-DEBUG/2026090101' --publication-root 'temp/vnfc-bexp-r01/debug-2026090101-publication'
```

The CLI rejects any different DEBUG stage, seed, or update count before reading the receipt or
touching roots. It reads the fresh receipt once, binds the current prebuilt artifacts into the exact
storage contract, creates one production process-tree telemetry sink, and invokes the public
runtime exactly once. It performs no retry. On success, its sole stdout record is the canonical
execution receipt. This DEBUG is the only result-bearing invocation currently open; PRIMARY and
OPTIONAL remain gated by its archived canonical three-piece bundle.

Both CLI paths use a pure-filesystem load-only resolver after fresh preflight validation. It walks
standard Program Files Visual Studio layouts with `pathlib`, hashes `cl.exe` candidates as files,
and never invokes `vswhere`, `cl.exe`, a subprocess, or an original build-capable helper. For each
unique compiler hash it recomputes the exact R09 and shadow keys from current source, contract,
science/public-law, frozen-flag, and ABI bytes. Exactly one pair with both cache DLLs must exist;
missing or ambiguous pairs are `REPAIR_REQUIRED`. The selected source/compiler/key/path/hash/size
facts install process-local validating load-only functions. Formal DEBUG resolves and installs this
binding before sink construction but performs actual DLL loading, ABI/magic validation, and shadow
embedded-fingerprint validation only after telemetry starts in the monitored source stage.
The installer is private and treats resolver output as untrusted: before changing any process
function or cache it independently re-enumerates and rehashes the regular non-reparse `cl.exe`,
rehashes live source inputs, recomputes both keys, checks exact DLL filenames/key-parent
directories, and rechecks absolute artifact paths, sizes, hashes, and reparse status. A forged or
stale binding therefore fails before global mutation, cache clearing, DLL loading, root access, or
monitor construction.

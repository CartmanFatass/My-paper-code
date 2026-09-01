# FRRIE B01 CM engineering milestone — 2026-09-01

## Engineering conclusion

The independent B01 contract, paired trainer primitives, checkpoint/resume codec,
evaluation-tape contract, create-once lifecycle, and TEST-only contract/checkpoint smoke exist.
No FRRIE-B01 scientific run was launched and no production seed packet or production root was
created. R01/R02 contracts and result namespaces remain locked and separate.

The production performance disposition is **`REPAIR_REQUIRED`**. The local Windows environment
does not expose `cl.exe`, so the actual package-native scalar/batch equivalence, deterministic
1/2/4-worker observation, and result-blind end-to-end training/evaluation telemetry have not been
formed. Production panel publication and the complete 28-quantity analysis are fail-closed while
those facts and exact inventory validators are absent.

## Implemented boundary

The B01 namespace is under
`experiments/candidates/finite_resource_relational_inductive_efficiency/b01/`. It binds the exact
experiment identity `FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901`, float32 model compute with
float64 reductions, the named C++ batch profile, the fixed optimizer/loss/projection contract,
canonical five-root packet semantics, initial/extension manifest rules, checkpoint 0 and resume,
common addressed evaluation tapes, TOP24 conversion, raw-control receipts, and create-only output
roots.

The paired update transaction rolls both arms back on any failed update or postcondition. Before
first contact, full paired model and optimizer state must be equal. After contact, model-derived
quantities and endogenous observations may legitimately differ; matching instead binds direct
exogenous tape bytes, host/observation/relation/mask function revisions, roles, legal-mask law,
origin coordinates, batch coordinates, and the actual 4,928-slot work ledger.

Production-complete panel validation intentionally refuses publication until exact training,
checkpoint-restore, action-probability, evaluation, and derived-quantity inventories are
implemented. The available analysis is descriptive/partial only and cannot interpret the
scientific branch.

## Verification

- B01-owned tests after the final source-state and optimizer-contract repair:
  `38 passed, 1 skipped`.
- Full FRRIE regression: `200 passed, 2 skipped`.
- The skips are the unavailable package-native/MSVC toolchain path; they are not accepted as
  scalar/batch or worker-equivalence evidence.
- Final retained TEST smoke receipt:
  `temp/frrie_b01_cm_contract_smoke_20260901_r2/admit-memory.json`.
- Receipt physical/effective available memory: `17,220,182,016` bytes; both 4 GiB floors passed.
- TEST packet and manifest:
  `temp/frrie_b01_cm_contract_smoke_20260901_r2/test-seed-packet.json` and
  `temp/frrie_b01_cm_contract_smoke_20260901_r2/test-manifest.json`.
- Retained checkpoint and smoke artifact:
  `temp/frrie_b01_cm_contract_smoke_20260901_r2/run/checkpoint/checkpoint-000.json` and
  `temp/frrie_b01_cm_contract_smoke_20260901_r2/run/output/smoke.json`.
- The smoke persisted checkpoint 0, reread its exact bytes, decoded it, and revalidated both live
  arm parameter bytes. A second invocation against the same roots was refused with exit code 2.
- The smoke artifact directly records `native_executed=false`, `environment_executed=false`,
  `update_executed=false`, `evaluation_executed=false`, and `scientific_values=null`.

The authoritative r2 TEST manifest records source state as base commit
`f198cedf8b0bb2c06b6e79ed3415e08b6e197477` plus
`worktree_state=DIRTY_UNCOMMITTED_TEST_ONLY`; it does not claim that the base commit contains the
new B01 code. Production manifests still require one exact full commit revision. The earlier
non-r2 TEST smoke used an ambiguous `code_revision` field and is retained only as a historical,
non-authoritative TEST artifact.

## Remaining production blockers

1. Restore the package-native C++ toolchain and directly establish scalar-versus-batch and stable
   1/2/4-worker equivalence on identical tapes, actions, states, observations, terminals,
   primitives, and work ledgers.
2. Complete a real package-native trainer/evaluator pilot with fresh per-invocation memory receipts
   and measured stage/end-to-end wall time, throughput, process-tree peak RSS, worker occupancy,
   scratch/durable peaks, and I/O.
3. Implement and validate the complete panel coordinate inventories and all frozen derived
   quantities before enabling production analysis or publication.
4. Reassess the performance disposition from direct measurements. Long production remains
   withheld while the disposition is `REPAIR_REQUIRED`.

For scale only, one initial seed contains 2,523,136 training slots per arm (5,046,272 across the
paired arms); the three-seed initial phase contains 15,138,816 paired-arm slots. These static work
counts are not runtime-feasibility evidence and are not a substitute for the missing native pilot.

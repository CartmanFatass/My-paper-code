# VNFC BPCR revision-09 TRAIN repair 02 technical acceptance

Direction: `variable_n_fleet_churn_b4`

Stage: `VNFC-BPCR-R09-FULL-EMPIRICAL-PANEL`, phase `TRAIN`

CM: `/root/cm_vnfc_uav_post_churn`

## Observed process defect and retained frontier

The first replacement TRAIN command completed the exact
`BPCR-REP-00.MAPR` 256-update slot and wrote its immutable final
checkpoint/optimizer. It then created the same-coordinate
`BPCR-REP-00.DIRECT` initial pair and exited with:

```text
RuntimeError: one of the variables needed for gradient computation has been modified by an inplace operation
```

DIRECT's residual scorer consumed the autoregressive prefix tensors. The
decoder then changed those saved tensors in place before backward. PyTorch
correctly rejected the saved-tensor version mismatch.

Under the frozen science card's indivisible activity block, partial arms,
checkpoints and worlds before the complete atomic manifest are not treatment
observations. No question-relevant scientific activity or partial
interpretation occurred. The complete MAPR slot and DIRECT initial pair remain
blinded same-coordinate frontier state for unchanged-science continuation.

## Accepted repair

- DIRECT prefix sum, maximum and presence state now use functional tensor
  updates. The mathematical state, token order, actions, fixed-token skipping
  and residual semantics are unchanged.
- An anomaly-detection regression completes DIRECT backward and its first
  optimizer step. With the residual output fixed at exact zero, DIRECT commands
  and token probabilities remain bitwise identical to containing MAPR.
- A completed slot is returned read-only only after validating the exact
  canonical generation inventory `g0001` through `g0256`, every frozen field,
  slot/address, contained state path, state SHA-256, cumulative counts,
  origin-bindings digest and predecessor digest chain.
- The generation-256 state must exactly match both final checkpoint and final
  optimizer. Missing, partial or mismatched finals fail closed.
- An incomplete slot validates the same exact chain through its last generation
  and resumes from that state. Existing initial pairs are validated and reused
  byte-for-byte.

The actual blinded `BPCR-REP-00.MAPR` frontier passed metadata-only independent
validation: 256 generation records, 256 state files, exact predecessor chain
and non-exposing origin metadata. No tensor, endpoint or scientific value was
loaded for that verification.

## Frozen replacement bindings

- Current source manifest: `FINAL`, 40 files, SHA-256
  `89f5cd04753130288eb819ef56359e7a93e29ef9559fc65af8a7806e11164e3c`.
- Preserved coordinate digest:
  `9a2a4affb03e4c2eb2ded763991fcbe9bfef18b6df19457b5ad67e2dce31e87b`.
- Preserved master digest:
  `9e5927ca82fda74e557eb38cf4af3b0d149ac0fef0f0d89319796aed4c6a64a9`.
- Origin lease ID: `VNFC-BPCR-R09-ROOT-TRAIN-20260821-01`.
- Exact exception, native source/artifact/build and shared source identities are
  unchanged from repair 01.
- The fresh-initial coordinate digest for the current manifest is
  `a1d757fa62a7cf25f167ab0b19eb823be3a141b7e06ffef20a4bd54d6fdf1053`;
  it is not used by this same-identity continuation.

## Validation

CM combined candidate and shared-policy command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09 tests/production_backend_policy_test.py -q --basetemp=.tmp/vnfc_bpcr_r09_cm_chain_repair_20260821_01
```

Result: `107 passed, 1 expected anomaly-detection warning in 97.16s`.

Independent disposition: `VERIFIED`. Its focused suite passed 34 tests and its
metadata-only audit accepted the actual 256-generation MAPR chain.

## Replacement TRAIN lease request 02

The prior terminal and acceptance files remain immutable. Continue with:

- lease path:
  `C:\Projects\HMASD\temp\leases\VNFC_BPCR_R09_ROOT_TRAIN_REPLACEMENT_LEASE_20260821_02.json`;
- new lease ID, with `replacement_of` and `origin_lease_id` both bound to
  `VNFC-BPCR-R09-ROOT-TRAIN-20260821-01`;
- preserved coordinate/master flags and digest unchanged;
- current source manifest `89f5cd04753130288eb819ef56359e7a93e29ef9559fc65af8a7806e11164e3c`;
- existing result root, frontier root and `RUN_IDENTITY.json`;
- CM acceptance `PREACTIVITY_ACCEPTANCE_REPAIR_02.json`;
- new TRAIN terminal `TRAIN_TERMINAL_REPAIR_02.json`;
- reserved EVALUATE terminal `EVALUATE_TERMINAL_REPAIR_02.json`;
- unchanged checkpoint-acceptance and complete-manifest paths;
- the exact registered Python/module `--phase TRAIN` command with only this
  replacement lease path; and
- the unchanged Root resource ceiling.

This record issues no lease and starts no process. EVALUATE remains ineligible
until all 32 learned slots complete, CM independently accepts all checkpoint
chains and Root issues a separate EVALUATE lease.

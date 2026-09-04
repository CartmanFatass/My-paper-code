# VNFC BPCR revision-09 TRAIN completion and checkpoint technical acceptance

```text
document_kind=direction_cm_train_checkpoint_technical_acceptance
owner=CM_variable_n_fleet_churn_b4
scope=direction:variable_n_fleet_churn_b4
stage=VNFC-BPCR-R09-FULL-EMPIRICAL-PANEL
phase=TRAIN
train_complete=true
checkpoint_barrier_technically_accepted=true
evaluation_started=false
partial_interpretation_permitted=false
```

## Conclusion

The unchanged-science TRAIN continuation completed under the existing
replacement lease and the complete 32-slot global checkpoint barrier is
technically accepted.

The command resumed the preserved blinded frontier at
`BPCR-REP-14.DIRECT.g0182.json`; it did not create a new coordinate, master,
seed, origin lease, result root, manifest identity or treatment. The retained
TRAIN command exited with code zero.

## Retained execution and barrier

- Command:
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.variable_n_fleet_churn_bpcr_r09 --phase TRAIN --lease C:\Projects\HMASD\temp\leases\VNFC_BPCR_R09_ROOT_TRAIN_REPLACEMENT_LEASE_20260821_02.json`.
- TRAIN terminal:
  `artifacts/VNFC_BPCR_R09_FUTURE/TRAIN_TERMINAL_REPAIR_02.json`, SHA-256
  `4273a752bff0e2e143e3fd0950d8effef714c0cd31a7e5dd544a2e5e8cb41088`.
- Global checkpoint acceptance:
  `artifacts/VNFC_BPCR_R09_FUTURE/CHECKPOINT_ACCEPTANCE.json`, SHA-256
  `f5c283ba77184041cbf6b522e733bf2517d667bd6a2a39f11d3ea1a81a21c7de`.
- Frozen source-manifest provenance:
  `89f5cd04753130288eb819ef56359e7a93e29ef9559fc65af8a7806e11164e3c`.
- Coordinate digest:
  `9a2a4affb03e4c2eb2ded763991fcbe9bfef18b6df19457b5ad67e2dce31e87b`.
- Master digest:
  `9e5927ca82fda74e557eb38cf4af3b0d149ac0fef0f0d89319796aed4c6a64a9`.
- Origin lease:
  `VNFC-BPCR-R09-ROOT-TRAIN-20260821-01`.

## Technical evidence

The CM acceptance pass validated, without reporting model or scientific
values:

- all 32 required replicate-arm slots at generation 256;
- every canonical generation address and predecessor/state-hash chain;
- every generation-256 state binding and update count;
- equality of each terminal generation's model and optimizer state with its
  retained final checkpoint and final optimizer;
- 64 unique checkpoint artifacts and 64 unique optimizer artifacts;
- 128 paths unique across both artifact classes;
- the frozen manifest, coordinate, master and origin binding on all 32
  receipts; and
- a successful independent parse and runtime-binding validation of the
  create-once checkpoint barrier.

The acceptance contains 32 externally accepted receipts and remains bound to
the frozen `c378997e...cf2e1b` frontier provenance while the candidate-local
alignment preflight validates authoritative live shared policy
`c79a26e4...939ce`.

## Local fence and next owner

No EVALUATE process was started, no EVALUATE terminal exists, and no complete
atomic manifest exists. No partial arm, replicate, checkpoint, endpoint or
scientific value was interpreted or returned.

EVALUATE now has its required external CM checkpoint barrier, but still
requires a separate Operational-Root-issued EVALUATE lease bound to this exact
barrier, manifest, coordinate, master, origin and result root. Operational Root
is the next owner for that lease decision; the same VNFC CM retains the later
unchanged-science EVALUATE execution and complete-manifest technical
acceptance.

# VNFC BPCR revision-09 TRAIN repair technical acceptance

Direction: `variable_n_fleet_churn_b4`

Stage: `VNFC-BPCR-R09-FULL-EMPIRICAL-PANEL`, phase `TRAIN`

CM: `/root/cm_vnfc_uav_post_churn`

## Observed process defect

The exact initial TRAIN command exited with code 1 before question-relevant
scientific activity began. It created the blinded run identity, frontier
bindings and the `BPCR-REP-00.MAPR` initial checkpoint/optimizer pair, then
raised:

```text
ValueError: pooling requires one nonempty finite binary64 matrix
```

The roster was not empty. Masked candidates have exact probability zero, but
the entropy expression evaluated `log(0)` inside a `torch.where`. The forward
value was masked while autograd still produced a NaN gradient. The first PPO
step therefore made parameters nonfinite, and the next exact binary64 roster
mean correctly rejected its nonfinite input.

This is an ordinary unchanged-science trainer defect. It supplies no evidence
about the treatment, comparator, direction or Portfolio investment.

## Accepted repair

- Zero-probability entropy terms now substitute probability one before the
  logarithm and contribute exact `0 log 0 = 0`. Positive-probability terms,
  actions, support, logits and loss semantics are unchanged.
- A pre-generation initial checkpoint/optimizer pair is loaded, hash-checked
  against the deterministic same-coordinate initialization, and reused
  byte-for-byte. It is never overwritten. A partial or mismatched pair fails
  closed.
- Initial Root leases remain bound to the current source manifest's coordinate
  proposal digest.
- A replacement Root lease binds the new source/native manifest while deriving
  the preserved coordinate digest, master digest and origin from the existing
  blinded `RUN_IDENTITY` and frontier bindings. Any coordinate, master, origin
  or lineage mismatch fails before resume effects.
- Replacement frontier resume may update only source/native bindings. The
  coordinate, master, origin, shared source, science card and public-law
  bindings remain immutable.

## Frozen replacement bindings

- Current empirical source manifest: `FINAL`, 40 files, SHA-256
  `7d63f58500812b2b8f41979aed6e36839f6b6304e440d9a21e8dc43f748164db`.
- Preserved coordinate proposal SHA-256:
  `9a2a4affb03e4c2eb2ded763991fcbe9bfef18b6df19457b5ad67e2dce31e87b`.
- Preserved master digest:
  `9e5927ca82fda74e557eb38cf4af3b0d149ac0fef0f0d89319796aed4c6a64a9`.
- Origin lease ID: `VNFC-BPCR-R09-ROOT-TRAIN-20260821-01`.
- Exact-object exception certificate:
  `da2b412f32b72e5fc6e34ad4af944a7337aae2b7ea2d9094d5fd06cfed67da6e`.
- Native source/artifact/build identities remain respectively
  `9a7e47bd416d4dba66c6e798dadc4157bbed372c72dc8fbd54a9852131a81656`,
  `e7c93817871ee70a925ca97d09bde34319ccbf11d52ad137f9ea0453903be407`
  and `aa2409b219ccec0c9d45f802729b12545fe511138400d36e3d057a003c05ea76`.
- Shared source remains
  `c378997ec45b599c19a34b7ce1c8cdecbd127f695aed7218a625dc8bebcf2e1b`.

The current-manifest digest for a hypothetical fresh initial identity is
`796595095bd5da714ae8455d507457734739751dbc8cd03c62250635f7e6ed57`.
It is not used for this continuation and must not replace the preserved
coordinate digest.

## Validation

CM combined candidate and shared-policy command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09 tests/production_backend_policy_test.py -q --basetemp=.tmp/vnfc_bpcr_r09_cm_train_repair_20260821_01
```

Result: `99 passed in 56.39s`.

An independent proof-sized verifier confirmed the root cause, exact entropy
repair, immutable initial-pair reuse and replacement-lineage validation. Its
focused suite returned `26 passed in 36.47s` and disposition `VERIFIED`.

## Replacement TRAIN lease request

The original TRAIN terminal is immutable and remains evidence. Continuation
requires a new Root lease file and new terminal/acceptance paths, while reusing
the exact result root, blinded identity and frontier:

- lease path:
  `C:\Projects\HMASD\temp\leases\VNFC_BPCR_R09_ROOT_TRAIN_REPLACEMENT_LEASE_20260821_01.json`;
- `replacement_of` and `origin_lease_id`:
  `VNFC-BPCR-R09-ROOT-TRAIN-20260821-01`;
- `preserve_coordinate_digest=true`, `preserve_master_digest=true`;
- `preserved_master_digest`:
  `9e5927ca82fda74e557eb38cf4af3b0d149ac0fef0f0d89319796aed4c6a64a9`;
- result root: `C:\Projects\HMASD\artifacts\VNFC_BPCR_R09_FUTURE`;
- frontier/root identity paths remain `frontiers` and `RUN_IDENTITY.json`;
- preactivity acceptance:
  `PREACTIVITY_ACCEPTANCE_REPAIR_01.json`;
- TRAIN terminal: `TRAIN_TERMINAL_REPAIR_01.json`;
- EVALUATE terminal reservation: `EVALUATE_TERMINAL_REPAIR_01.json`;
- checkpoint acceptance and complete-manifest paths remain
  `CHECKPOINT_ACCEPTANCE.json` and `COMPLETE_MANIFEST.json`;
- exact command remains the registered Python/module `--phase TRAIN`, with only
  the replacement lease path changed;
- the original CPU/resource ceiling remains unchanged.

This acceptance does not itself issue a lease or restart TRAIN. EVALUATE
remains forbidden until complete TRAIN, external CM checkpoint acceptance and
a separate Root EVALUATE lease.

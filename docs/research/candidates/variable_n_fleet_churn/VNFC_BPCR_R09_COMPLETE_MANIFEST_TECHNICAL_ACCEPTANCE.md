# VNFC BPCR revision-09 complete-manifest technical acceptance

```text
document_kind=direction_cm_complete_manifest_technical_acceptance
owner=CM_variable_n_fleet_churn_b4
scope=direction:variable_n_fleet_churn_b4
stage=VNFC-BPCR-R09-FULL-EMPIRICAL-PANEL
train_complete=true
evaluate_complete=true
complete_manifest_technically_accepted=true
partial_interpretation_permitted=false
scientific_interpretation_owner=Portfolio-owned same-direction EM
```

## Conclusion

The exact unchanged-science revision-09 empirical execution is technically
complete. The repaired EVALUATE command exited with code zero and published
one create-once complete atomic manifest. CM independently validated the full
manifest, its checkpoint barrier, all registered artifact categories and the
preserved run lineage without reporting or interpreting any scientific value.

## Accepted retained result

- Complete atomic manifest:
  `artifacts/VNFC_BPCR_R09_FUTURE/COMPLETE_MANIFEST.json`, SHA-256
  `270d4b31599c44e7395c458f89335bde8adf6afd224d749f55c7db59fd74ebd7`.
- Successful EVALUATE terminal:
  `artifacts/VNFC_BPCR_R09_FUTURE/EVALUATE_TERMINAL_REPAIR_04.json`, SHA-256
  `8d0f2d3bbc9457746a9cad076ef5fee0f56a37e8c6efced8b1967a360517e7f3`.
- Accepted checkpoint barrier:
  `artifacts/VNFC_BPCR_R09_FUTURE/CHECKPOINT_ACCEPTANCE.json`, SHA-256
  `f5c283ba77184041cbf6b522e733bf2517d667bd6a2a39f11d3ea1a81a21c7de`.
- Frozen source-manifest identity:
  `89f5cd04753130288eb819ef56359e7a93e29ef9559fc65af8a7806e11164e3c`.
- Coordinate digest:
  `9a2a4affb03e4c2eb2ded763991fcbe9bfef18b6df19457b5ad67e2dce31e87b`.
- Master digest:
  `9e5927ca82fda74e557eb38cf4af3b0d149ac0fef0f0d89319796aed4c6a64a9`.
- Origin lease:
  `VNFC-BPCR-R09-ROOT-TRAIN-20260821-01`.
- Result root:
  `C:\Projects\HMASD\artifacts\VNFC_BPCR_R09_FUTURE`.

The manifest retains `complete=true` and
`partial_interpretation_permitted=false`.

## CM validation

The final acceptance pass established:

- canonical complete-manifest bytes and exact schema;
- exact frozen manifest, native, coordinate, master, origin and frontier
  bindings;
- the accepted 32-slot checkpoint barrier and its exact digest;
- all 32 generation-256 frontier predecessor hashes;
- all 17 registered atomic artifact categories;
- exact category index and child hashes;
- exact registered logical cardinalities for every category; and
- recursive category schema/binding/cardinality validity.

No category payload value was summarized, compared scientifically, or emitted
by CM. Validation was limited to lifecycle, schema, binding, hash and
cardinality acceptance.

## Unchanged-science EVALUATE repairs

Two pre-manifest EVALUATE failures remain preserved in immutable terminal
records. Neither wrote a result artifact or complete manifest.

The accepted mechanical repairs were:

1. a support-valid teacher-forced action in the DIRECT zero-residual
   diagnostic may have an exactly zero floating-point probability through
   underflow; the evaluation-only path now validates actual masked support and
   uses stable log-softmax, while default/free/training behavior remains on the
   original path; and
2. the deterministic decoder's non-best sentinel previously equaled the null
   candidate's tie rank, allowing a unique-null-best decision to select an
   unsupported row; non-best candidates now use the integer maximum while the
   frozen null and opaque-rank ordering is unchanged.

Both repairs received independent read-only material-risk approval. The final
focused candidate/training/shared-policy suite completed with `111 passed` and
one expected anomaly-detection warning.

Final candidate-local repair identities are:

- `torch_models.py`:
  `e12275f192bcf358aab2b1d23be2b8129f9be3a952dda80ddfc4b27fa2a4e462`;
- `evaluation.py`:
  `563cf3dad9859f22e35c905d4c5311362ebdde7385b8d53a1d1d1fde1a25d01c`;
- `source_manifest.py`:
  `afd9b669ae0bd12c5597dfaf11b486637c781042592845917c299c72b270005e`;
- `shared_source_alignment_transition.json`:
  `ae8407604f4fc466ce5d91b2e4ffe2394081e4b6ddb14951005615574021a863`;
  and
- focused preactivity/model test:
  `b825bc7dabcdbb8925be86c90e9dc37587c10e306eb8246f19f68e0d43ca80db`.

The validation-only source transition continues to preserve the frozen
`c378997e...cf2e1b` frontier provenance while validating authoritative live
shared policy `c79a26e4...939ce`. It grants no lease or activity authority.

## Handoff boundary

CM technical acceptance is complete. No new VNFC run, treatment, lease,
coordinate, seed, threshold, comparator or follow-on action is authorized by
this record.

Operational Root is the next owner for exact relay of this CM-authored artifact
and retained complete-manifest path to the dedicated Portfolio session. The
Portfolio-owned same-direction EM alone may inspect and interpret the complete
scientific result, establish the claim boundary, and coordinate the required
same-conversation Pro result convergence.
